from __future__ import annotations

import json
import os
import subprocess
import tempfile
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

            return ExecutionResult(returncode, tuple(tail))
        finally:
            job_file.unlink(missing_ok=True)
