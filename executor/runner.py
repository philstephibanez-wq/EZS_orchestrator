from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .planner import ExecutionPlan


@dataclass(frozen=True, slots=True)
class ProcessResult:
    returncode: int
    stdout: str


class SubprocessRunner:
    """Generic subprocess runner.

    Analysis-specific command construction belongs to the EZScore analysis entrypoint,
    not here.
    """

    def run_job_file(self, plan: ExecutionPlan, job_file: Path, timeout: float | None = None) -> ProcessResult:
        command = [
            str(plan.python),
            str(plan.entrypoint),
            "--job-file",
            str(job_file),
        ]
        proc = subprocess.run(
            command,
            cwd=str(plan.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return ProcessResult(returncode=proc.returncode, stdout=proc.stdout)
