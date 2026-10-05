from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from capability.publisher import AnalysisCapabilityPublisher
from config.loader import load_runtime_config
from contracts.target import Target
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

from .singleton import ServiceSingleton


JOB_ID_RE = re.compile(r"\bjob_id=(\d+)\b")
EVENT_JOB_ID_RE = re.compile(r'"job_id"\s*:\s*(\d+)')


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def targets_for_scope(target: Target | None) -> tuple[Target, ...]:
    return (Target.DEV, Target.PROD) if target is None else (target,)


class PermanentRunner:
    """Permanent orchestration service.

    target=None means the single machine-wide service serves DEV and PROD.
    A concrete target remains supported for focused diagnostics/tests.

    The service stays sequential, therefore the existing machine-wide GPU
    singleton contract remains intact.
    """

    def __init__(
        self,
        target: Target | None,
        *,
        poll_seconds: float = 2.0,
        max_backoff_seconds: float = 30.0,
    ):
        self.config = load_runtime_config()
        self.target = target
        self.targets = targets_for_scope(target)
        self.scope = target.value if target is not None else "all"
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
        self.publisher = AnalysisCapabilityPublisher(self.config)
        self._stop = False
        self._cursor = 0
        self._last_reachable = {target: False for target in self.targets}

    def request_stop(self, *_args) -> None:
        self._stop = True

    def install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self.request_stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self.request_stop)

    def write_heartbeat(self, state: str, **extra) -> None:
        payload = {
            "schema": "ezs.orchestrator.heartbeat.v2",
            "pid": os.getpid(),
            "target": self.scope,
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

    def publish(
        self,
        target: Target,
        *,
        available: bool,
        state: str,
        queued: int | None = None,
        active_target: str | None = None,
        error: str | None = None,
    ) -> None:
        self.publisher.publish(
            target,
            available=available,
            state=state,
            service_scope=self.scope,
            queued=queued,
            active_target=active_target,
            error=error,
        )

    def should_stop(self) -> bool:
        return self._stop or self.stop_file.exists()

    def _extract_job_id(self, text: str) -> int | None:
        m = JOB_ID_RE.search(text) or EVENT_JOB_ID_RE.search(text)
        return int(m.group(1)) if m else None

    def _persist_attempt(
        self,
        *,
        target: Target,
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
            / target.value
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
                    "target": target.value,
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

    def _busy_heartbeat_loop(
        self,
        stop_event: threading.Event,
        active_target: Target,
        queued_by_target: dict[Target, int],
    ) -> None:
        while not stop_event.wait(self.poll_seconds):
            self.write_heartbeat(
                "dispatch",
                active_target=active_target.value,
                queued={t.value: queued_by_target.get(t, 0) for t in self.targets},
            )
            for target in self.targets:
                if target is active_target:
                    self.publish(
                        target,
                        available=True,
                        state="busy",
                        queued=queued_by_target.get(target, 0),
                        active_target=active_target.value,
                    )
                elif self._last_reachable.get(target, False):
                    self.publish(
                        target,
                        available=True,
                        state="waiting",
                        queued=queued_by_target.get(target, 0),
                        active_target=active_target.value,
                    )
                else:
                    self.publish(
                        target,
                        available=False,
                        state="target_unreachable",
                        queued=None,
                        active_target=active_target.value,
                    )

    def run_one_child(
        self,
        target: Target,
        queued_by_target: dict[Target, int],
    ) -> tuple[int, Path]:
        attempt_id = f"{utc_stamp()}-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc).isoformat()

        cmd = [
            sys.executable,
            "-m",
            "control_center.cli",
            "run-once",
            "--target",
            target.value,
        ]

        stop_event = threading.Event()
        heartbeat_thread = threading.Thread(
            target=self._busy_heartbeat_loop,
            args=(stop_event, target, queued_by_target),
            name="ezs-analysis-capability-heartbeat",
            daemon=True,
        )
        heartbeat_thread.start()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.config.orchestrator_root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
            )
        finally:
            stop_event.set()
            heartbeat_thread.join(timeout=max(2.0, self.poll_seconds * 2))

        ended_at = datetime.now(timezone.utc).isoformat()
        attempt_dir = self._persist_attempt(
            target=target,
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

    def _ordered_targets(self) -> tuple[Target, ...]:
        if len(self.targets) <= 1:
            return self.targets
        ordered = self.targets[self._cursor :] + self.targets[: self._cursor]
        return ordered

    def _advance_after(self, target: Target) -> None:
        if len(self.targets) <= 1:
            return
        idx = self.targets.index(target)
        self._cursor = (idx + 1) % len(self.targets)

    def run_forever(self) -> int:
        self.singleton.acquire(
            target=self.scope,
            poll_seconds=self.poll_seconds,
        )
        self.install_signal_handlers()
        self.stop_file.unlink(missing_ok=True)

        for target in self.targets:
            self.publish(target, available=False, state="starting")

        try:
            self.write_heartbeat("starting")
            while not self.should_stop():
                queues: dict[Target, list] = {}
                queue_counts: dict[Target, int] = {}
                errors: dict[Target, str] = {}

                # Probe every target before dispatch. A failure of one target
                # never marks the other target unavailable.
                for target in self.targets:
                    try:
                        jobs = self.transport.queue(target)
                        queues[target] = jobs
                        queue_counts[target] = len(jobs)
                        self._last_reachable[target] = True
                        self.publish(
                            target,
                            available=True,
                            state="queued" if jobs else "idle",
                            queued=len(jobs),
                        )
                    except Exception as exc:
                        error = str(exc)[:500]
                        errors[target] = error
                        self._last_reachable[target] = False
                        self.publish(
                            target,
                            available=False,
                            state="transport_error",
                            error=error,
                        )

                selected: Target | None = None
                for target in self._ordered_targets():
                    if queues.get(target):
                        selected = target
                        break

                if selected is None:
                    state = "idle" if any(self._last_reachable.values()) else "transport_error"
                    self.write_heartbeat(
                        state,
                        queued={t.value: queue_counts.get(t) for t in self.targets},
                        errors={t.value: errors[t] for t in errors},
                    )
                    time.sleep(self.poll_seconds)
                    continue

                self._advance_after(selected)
                self.write_heartbeat(
                    "dispatch",
                    active_target=selected.value,
                    queued={t.value: queue_counts.get(t, 0) for t in self.targets},
                )
                for target in self.targets:
                    if target is selected:
                        self.publish(
                            target,
                            available=True,
                            state="busy",
                            queued=queue_counts.get(target, 0),
                            active_target=selected.value,
                        )
                    elif self._last_reachable.get(target, False):
                        self.publish(
                            target,
                            available=True,
                            state="waiting",
                            queued=queue_counts.get(target, 0),
                            active_target=selected.value,
                        )

                rc, attempt_dir = self.run_one_child(selected, queue_counts)

                self.publish(
                    selected,
                    available=True,
                    state="last_attempt",
                    queued=max(0, queue_counts.get(selected, 1) - 1),
                    active_target=None,
                    error=None if rc == 0 else f"returncode={rc}",
                )
                self.write_heartbeat(
                    "last_attempt",
                    active_target=selected.value,
                    returncode=rc,
                    attempt_log=str(attempt_dir),
                )

                if rc != 0:
                    time.sleep(self.poll_seconds)

            self.write_heartbeat("stopping")
            return 0
        finally:
            for target in self.targets:
                try:
                    self.publish(target, available=False, state="stopped")
                except Exception:
                    pass
            self.singleton.release()
            self.stop_file.unlink(missing_ok=True)
            self.write_heartbeat("stopped")
