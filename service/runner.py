from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config.loader import load_runtime_config
from contracts.target import Target
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

from .singleton import ServiceSingleton


JOB_ID_RE = re.compile(r"\bjob_id=(\d+)\b")
EVENT_JOB_ID_RE = re.compile(r'"job_id"\s*:\s*(\d+)')


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


class PermanentRunner:
    def __init__(
        self,
        target: Target,
        *,
        poll_seconds: float = 2.0,
        max_backoff_seconds: float = 30.0,
    ):
        self.config = load_runtime_config()
        self.target = target
        self.poll_seconds = max(0.5, float(poll_seconds))
        self.max_backoff_seconds = max(
            self.poll_seconds,
            float(max_backoff_seconds),
        )
        self.transport = JobTransport(TargetRegistry(self.config))
        self.runtime_root = self.config.orchestrator_root / "runtime"
        self.service_dir = self.runtime_root / "service"
        self.service_dir.mkdir(parents=True, exist_ok=True)
        self.stop_file = self.service_dir / "stop.request"
        self.heartbeat_file = self.service_dir / "heartbeat.json"
        self.singleton = ServiceSingleton(self.runtime_root)
        self._stop = False

    def request_stop(self, *_args) -> None:
        self._stop = True

    def install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self.request_stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self.request_stop)

    def write_heartbeat(self, state: str, **extra) -> None:
        payload = {
            "schema": "ezs.orchestrator.heartbeat.v1",
            "pid": os.getpid(),
            "target": self.target.value,
            "state": state,
            "at": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        tmp = self.heartbeat_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.heartbeat_file)

    def should_stop(self) -> bool:
        return self._stop or self.stop_file.exists()

    def _extract_job_id(self, text: str) -> int | None:
        m = JOB_ID_RE.search(text) or EVENT_JOB_ID_RE.search(text)
        return int(m.group(1)) if m else None

    def _persist_attempt(
        self,
        *,
        attempt_id: str,
        started_at: str,
        ended_at: str,
        returncode: int,
        stdout: str,
        stderr: str,
    ) -> Path:
        combined = stdout
        if stderr:
            combined += ("\n" if combined and not combined.endswith("\n") else "")
            combined += "[stderr]\n" + stderr

        job_id = self._extract_job_id(combined)
        job_segment = str(job_id) if job_id is not None else "_unknown"
        attempt_dir = (
            self.runtime_root
            / "jobs"
            / self.target.value
            / job_segment
            / attempt_id
        )
        attempt_dir.mkdir(parents=True, exist_ok=True)

        (attempt_dir / "execution.log").write_text(
            combined,
            encoding="utf-8",
        )
        (attempt_dir / "result.json").write_text(
            json.dumps(
                {
                    "schema": "ezs.execution-attempt.v1",
                    "attempt_id": attempt_id,
                    "target": self.target.value,
                    "job_id": job_id,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "returncode": returncode,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        return attempt_dir

    def run_one_child(self) -> tuple[int, Path]:
        attempt_id = f"{utc_stamp()}-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc).isoformat()

        cmd = [
            sys.executable,
            "-m",
            "control_center.cli",
            "run-once",
            "--target",
            self.target.value,
        ]

        proc = subprocess.run(
            cmd,
            cwd=str(self.config.orchestrator_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )

        ended_at = datetime.now(timezone.utc).isoformat()
        attempt_dir = self._persist_attempt(
            attempt_id=attempt_id,
            started_at=started_at,
            ended_at=ended_at,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )

        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        print(f"attempt_log={attempt_dir}")

        return proc.returncode, attempt_dir

    def run_forever(self) -> int:
        self.singleton.acquire(
            target=self.target.value,
            poll_seconds=self.poll_seconds,
        )
        self.install_signal_handlers()
        self.stop_file.unlink(missing_ok=True)

        backoff = self.poll_seconds
        try:
            self.write_heartbeat("starting")
            while not self.should_stop():
                try:
                    jobs = self.transport.queue(self.target)
                except Exception as exc:
                    self.write_heartbeat(
                        "transport_error",
                        error=str(exc)[:500],
                        backoff_seconds=backoff,
                    )
                    time.sleep(backoff)
                    backoff = min(
                        self.max_backoff_seconds,
                        max(self.poll_seconds, backoff * 2),
                    )
                    continue

                backoff = self.poll_seconds

                if not jobs:
                    self.write_heartbeat("idle", queued=0)
                    time.sleep(self.poll_seconds)
                    continue

                self.write_heartbeat(
                    "dispatch",
                    queued=len(jobs),
                )
                rc, attempt_dir = self.run_one_child()

                self.write_heartbeat(
                    "last_attempt",
                    queued=len(jobs),
                    returncode=rc,
                    attempt_log=str(attempt_dir),
                )

                # Avoid a hot loop when a job repeatedly fails.
                if rc != 0:
                    time.sleep(self.poll_seconds)

            self.write_heartbeat("stopping")
            return 0
        finally:
            self.singleton.release()
            self.stop_file.unlink(missing_ok=True)
            self.write_heartbeat("stopped")
