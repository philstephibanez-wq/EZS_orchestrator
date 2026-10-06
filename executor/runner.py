from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from config.loader import RuntimeConfig
from contracts.job import JobEnvelope
from .planner import ExecutionPlanner, ExecutionPlan

WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout_tail: tuple[str, ...]


class JobExecutor:
    """Generic job process executor.

    It knows only the versioned EZScore worker entrypoint.
    It never constructs stems/chords/lyrics commands.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.planner = ExecutionPlanner(config)
        self.runtime_jobs = config.orchestrator_root / "runtime" / "jobs"
        self.runtime_jobs.mkdir(parents=True, exist_ok=True)

    def _write_job_file(self, job: JobEnvelope) -> Path:
        payload = job.to_dict()
        fd, name = tempfile.mkstemp(
            prefix=f"job-{job.job_id}-",
            suffix=".json",
            dir=str(self.runtime_jobs),
            text=True,
        )
        os.close(fd)
        path = Path(name)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _validate_runtime_files(plan: ExecutionPlan) -> None:
        if not plan.python.is_file():
            raise RuntimeError(
                f"analysis_python_missing:{plan.target.value}:{plan.python}"
            )
        if not plan.entrypoint.is_file():
            raise RuntimeError(
                f"analysis_entrypoint_missing:{plan.target.value}:{plan.entrypoint}"
            )

    def run(
        self,
        job: JobEnvelope,
        *,
        on_output: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        plan = self.planner.plan(job)

        # Runtime availability is checked after topology planning but before
        # creating an envelope file or spawning a process. R3.3 will publish
        # this exception as a failed claimed job; there is no cross-target
        # Python fallback.
        self._validate_runtime_files(plan)

        job_file = self._write_job_file(job)
        env = os.environ.copy()
        env["EZS_TARGET"] = job.target.value
        env["EZS_EXPECTED_ROOT"] = str(plan.project_root)
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        command = [
            str(plan.python),
            str(plan.entrypoint),
            "--job-file",
            str(job_file),
        ]

        raw_progress_path = (getattr(job, "paths", None) or {}).get("progress_file")
        progress_path = Path(str(raw_progress_path)) if raw_progress_path else None
        progress_baseline_mtime_ns = None
        if progress_path is not None:
            try:
                progress_baseline_mtime_ns = progress_path.stat().st_mtime_ns
            except OSError:
                pass

        tail: list[str] = []
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(plan.cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=WINDOWS_NO_WINDOW if os.name == "nt" else 0,
            )

            stop_progress = threading.Event()
            progress_thread: threading.Thread | None = None

            if on_progress is not None and progress_path is not None:
                def watch_progress() -> None:
                    last_percent: int | None = None
                    while not stop_progress.is_set():
                        try:
                            stat = progress_path.stat()
                            if (
                                progress_baseline_mtime_ns is not None
                                and stat.st_mtime_ns == progress_baseline_mtime_ns
                            ):
                                stop_progress.wait(0.20)
                                continue

                            payload = json.loads(progress_path.read_text(encoding="utf-8"))
                            percent = int(payload.get("percent", 0))
                            percent = max(0, min(100, percent))
                            if percent != last_percent:
                                try:
                                    on_progress(percent)
                                except Exception as exc:
                                    if on_output is not None:
                                        on_output(
                                            "progress_callback_error:"
                                            f"{type(exc).__name__}:{exc}"
                                        )
                                last_percent = percent
                        except (OSError, ValueError, TypeError, json.JSONDecodeError):
                            pass
                        stop_progress.wait(0.20)

                progress_thread = threading.Thread(
                    target=watch_progress,
                    name=f"ezs-progress-{job.job_id}",
                    daemon=True,
                )
                progress_thread.start()

            try:
                if proc.stdout is not None:
                    for line in proc.stdout:
                        text = line.rstrip()
                        if text:
                            tail.append(text)
                            tail = tail[-30:]
                            if on_output:
                                on_output(text)
                returncode = int(proc.wait(timeout=timeout))
            except Exception:
                if proc.poll() is None:
                    proc.terminate()
                raise
            finally:
                stop_progress.set()
                if progress_thread is not None:
                    progress_thread.join(timeout=1.0)

            return ExecutionResult(returncode, tuple(tail))
        finally:
            job_file.unlink(missing_ok=True)
