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
from runtime_support.atomic_json import atomic_write_json
from config.loader import load_runtime_config
from contracts.target import Target
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

from .singleton import ServiceSingleton


JOB_ID_RE = re.compile(r"\bjob_id=(\d+)\b")
EVENT_JOB_ID_RE = re.compile(r'"job_id"\s*:\s*(\d+)')


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def _safe_stream_write(stream, value: str) -> None:
    if not value:
        return
    encoding = getattr(stream, "encoding", None) or "utf-8"
    safe = value.encode(encoding, errors="backslashreplace").decode(encoding)
    stream.write(safe)
    stream.flush()


def targets_for_scope(target: Target | None) -> tuple[Target, ...]:
    return (Target.DEV, Target.PROD, Target.LAB) if target is None else (target,)


class PermanentRunner:
    """Permanent orchestration service.

    target=None means the single machine-wide service serves DEV, PROD and LAB.
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
        try:
            atomic_write_json(self.heartbeat_file, payload)
        except OSError as exc:
            print(
                "HEARTBEAT_WRITE_WARNING "
                f"path={self.heartbeat_file} "
                f"error={type(exc).__name__}:{exc}",
                file=sys.stderr,
                flush=True,
            )

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

    @staticmethod
    def _queue_job_meta(queued_job: dict | None) -> dict:
        row = queued_job if isinstance(queued_job, dict) else {}
        song = row.get("song") if isinstance(row.get("song"), dict) else {}
        return {
            "job_id": row.get("job_id"),
            "kind": row.get("kind"),
            "song_id": row.get("song_id"),
            "song_title": row.get("title") or song.get("title"),
        }

    def _begin_attempt(self, *, target: Target, attempt_id: str, started_at: str, queued_job: dict | None) -> Path:
        meta = self._queue_job_meta(queued_job)
        job_id = meta.get("job_id")
        try:
            job_id = int(job_id) if job_id is not None else None
        except (TypeError, ValueError):
            job_id = None
        job_segment = str(job_id) if job_id is not None else "_unknown"
        attempt_dir = self.runtime_root / "jobs" / target.value / job_segment / attempt_id
        attempt_dir.mkdir(parents=True, exist_ok=True)
        (attempt_dir / "execution.log").write_text("", encoding="utf-8")
        (attempt_dir / "result.json").write_text(json.dumps({
            "schema": "ezs.execution-attempt.v2",
            "attempt_id": attempt_id,
            "target": target.value,
            "job_id": job_id,
            "kind": meta.get("kind"),
            "song_id": meta.get("song_id"),
            "song_title": meta.get("song_title"),
            "state": "running",
            "started_at": started_at,
            "ended_at": None,
            "analysis_returncode": None,
            "finalize_status": "pending",
            "returncode": None,
            "error": None,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return attempt_dir

    def _persist_attempt(self, *, target: Target, attempt_dir: Path, attempt_id: str, started_at: str, ended_at: str, returncode: int, stdout: str, stderr: str, queued_job: dict | None) -> Path:
        combined = stdout
        if stderr:
            combined += ("\n" if combined and not combined.endswith("\n") else "")
            combined += "[stderr]\n" + stderr
        queue_meta = self._queue_job_meta(queued_job)
        operator_meta = {}
        finalize_meta = {}
        for line in combined.splitlines():
            try:
                parsed = json.loads(line)
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue
            if parsed.get("event") == "job_meta":
                operator_meta = parsed
            elif parsed.get("event") == "job_finalize_error":
                finalize_meta = parsed
        job_id = operator_meta.get("job_id", queue_meta.get("job_id"))
        if job_id is None:
            job_id = self._extract_job_id(combined)
        try:
            job_id = int(job_id) if job_id is not None else None
        except (TypeError, ValueError):
            job_id = None
        kind = operator_meta.get("kind") or queue_meta.get("kind")
        song_id = operator_meta.get("song_id") if operator_meta.get("song_id") is not None else queue_meta.get("song_id")
        song_title = operator_meta.get("song_title") or queue_meta.get("song_title")
        if finalize_meta:
            state = "finalize_error"
            analysis_returncode = 0
            finalize_status = "error"
            error = str(finalize_meta.get("error") or "complete_callback_failed")[:500]
        elif returncode == 0:
            state = "completed"
            analysis_returncode = 0
            finalize_status = "ok"
            error = None
        else:
            state = "failed"
            analysis_returncode = returncode
            finalize_status = "not_attempted"
            error = None
        (attempt_dir / "execution.log").write_text(combined, encoding="utf-8")
        (attempt_dir / "result.json").write_text(json.dumps({
            "schema": "ezs.execution-attempt.v2",
            "attempt_id": attempt_id,
            "target": target.value,
            "job_id": job_id,
            "kind": kind,
            "song_id": song_id,
            "song_title": song_title,
            "state": state,
            "started_at": started_at,
            "ended_at": ended_at,
            "analysis_returncode": analysis_returncode,
            "finalize_status": finalize_status,
            "returncode": returncode,
            "error": error,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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

    def run_one_child(self, target: Target, queued_by_target: dict[Target, int], queued_job: dict | None = None) -> tuple[int, Path]:
        attempt_id = f"{utc_stamp()}-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc).isoformat()
        attempt_dir = self._begin_attempt(target=target, attempt_id=attempt_id, started_at=started_at, queued_job=queued_job)
        cmd = [sys.executable, "-m", "control_center.cli", "run-once", "--target", target.value]
        stop_event = threading.Event()
        heartbeat_thread = threading.Thread(target=self._busy_heartbeat_loop, args=(stop_event, target, queued_by_target), name="ezs-analysis-capability-heartbeat", daemon=True)
        heartbeat_thread.start()
        try:
            proc = subprocess.run(cmd, cwd=str(self.config.orchestrator_root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace")
        finally:
            stop_event.set()
            heartbeat_thread.join(timeout=max(2.0, self.poll_seconds * 2))
        ended_at = datetime.now(timezone.utc).isoformat()
        attempt_dir = self._persist_attempt(target=target, attempt_dir=attempt_dir, attempt_id=attempt_id, started_at=started_at, ended_at=ended_at, returncode=proc.returncode, stdout=proc.stdout or "", stderr=proc.stderr or "", queued_job=queued_job)
        if proc.stdout:
            _safe_stream_write(sys.stdout, proc.stdout)
        if proc.stderr:
            _safe_stream_write(sys.stderr, proc.stderr)
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

                queued_job = queues.get(selected, [None])[0]
                rc, attempt_dir = self.run_one_child(selected, queue_counts, queued_job=queued_job)

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
