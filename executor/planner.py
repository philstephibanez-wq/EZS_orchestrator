from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.job import JobEnvelope
from contracts.target import Target


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    job_id: int
    target: Target
    project_root: Path
    python: Path
    entrypoint: Path
    cwd: Path


class ExecutionPlanner:
    """Resolve the target checkout before execution.

    This module does not implement any analysis algorithm.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config

    @staticmethod
    def _resolved(path: Path) -> Path:
        return path.resolve(strict=False)

    @staticmethod
    def _is_under(path: Path, root: Path) -> bool:
        try:
            path.resolve(strict=False).relative_to(root.resolve(strict=False))
            return True
        except ValueError:
            return False

    def root_for(self, target: Target) -> Path:
        return self.config.dev.root if target is Target.DEV else self.config.prod.root

    def forbidden_root_for(self, target: Target) -> Path:
        return self.config.prod.root if target is Target.DEV else self.config.dev.root

    def validate_external_path(self, job: JobEnvelope, path: Path) -> None:
        forbidden = self.forbidden_root_for(job.target)
        if self._is_under(path, forbidden):
            raise RuntimeError(
                f"Cross-root path forbidden for {job.target.value}: {path}"
            )

    def plan(self, job: JobEnvelope) -> ExecutionPlan:
        job.validate()
        root = self.root_for(job.target)
        entrypoint = root / self.config.analysis_entrypoint

        # The analysis code MUST be owned by the target checkout.
        if not self._is_under(entrypoint, root):
            raise RuntimeError("Analysis entrypoint escaped target root")

        return ExecutionPlan(
            job_id=job.job_id,
            target=job.target,
            project_root=root,
            python=self.config.analysis_python,
            entrypoint=entrypoint,
            cwd=root,
        )
