from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    def __init__(self, config: RuntimeConfig):
        self.config = config

    @staticmethod
    def _resolved(path: Path) -> Path:
        return path.resolve(strict=False)

    @classmethod
    def _is_under(cls, path: Path, root: Path) -> bool:
        try:
            cls._resolved(path).relative_to(cls._resolved(root))
            return True
        except ValueError:
            return False

    def root_for(self, target: Target) -> Path:
        if target is Target.DEV:
            return self.config.dev.root
        if target is Target.PROD:
            return self.config.prod.root
        lab = getattr(self.config, "lab", None)
        if target is Target.LAB and lab is not None:
            return lab.root
        raise ValueError(f"Unsupported target root: {target!r}")

    def forbidden_roots_for(self, target: Target) -> tuple[Path, ...]:
        roots = [self.config.dev.root, self.config.prod.root]
        lab = getattr(self.config, "lab", None)
        if lab is not None:
            roots.append(lab.root)
        owned = self.root_for(target)
        return tuple(root for root in roots if self._resolved(root) != self._resolved(owned))

    def python_for(self, target: Target) -> Path:
        return self.config.analysis_python_for(target)

    def validate_external_path(self, job: JobEnvelope, path: Path) -> None:
        for forbidden in self.forbidden_roots_for(job.target):
            if self._is_under(path, forbidden):
                raise RuntimeError(
                    f"Cross-root path forbidden for {job.target.value}: {path}"
                )

    def validate_payload_paths(self, job: JobEnvelope, value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                self.validate_payload_paths(job, nested)
            return
        if isinstance(value, (list, tuple)):
            for nested in value:
                self.validate_payload_paths(job, nested)
            return
        if not isinstance(value, str):
            return

        if len(value) >= 3 and value[1:3] in {":\\", ":/"}:
            self.validate_external_path(job, Path(value))

    def _validate_job_structures(self, job: JobEnvelope) -> None:
        for name in ("payload", "paths", "request", "song"):
            value = getattr(job, name, None)
            if value is not None:
                self.validate_payload_paths(job, value)

    def _validate_python_ownership(
        self,
        target: Target,
        python_path: Path,
        root: Path,
    ) -> None:
        """Validate topology only.

        File-system availability is an execution concern and is checked by
        JobExecutor immediately before spawning. Keeping existence out of the
        planner makes architecture contracts deterministic/offline while still
        preserving fail-closed runtime behavior.
        """
        for forbidden in self.forbidden_roots_for(target):
            if self._is_under(python_path, forbidden):
                raise RuntimeError(
                    f"Cross-root analysis Python forbidden for {target.value}: "
                    f"{python_path}"
                )

        if target is Target.LAB:
            configured = getattr(self.config, "lab_analysis_python", None)
            if configured is None or self._resolved(python_path) != self._resolved(configured):
                raise RuntimeError(
                    f"LAB analysis Python must match configured executable: {python_path}"
                )
            return

        if not self._is_under(python_path, root):
            raise RuntimeError(
                f"Analysis Python must be owned by {target.value} checkout: "
                f"{python_path}"
            )

    def plan(self, job: JobEnvelope) -> ExecutionPlan:
        job.validate()
        self._validate_job_structures(job)

        root = self.root_for(job.target)
        python = self.python_for(job.target)
        self._validate_python_ownership(job.target, python, root)

        entrypoint = root / self.config.analysis_entrypoint
        if not self._is_under(entrypoint, root):
            raise RuntimeError("Analysis entrypoint escaped target root")

        return ExecutionPlan(
            job_id=job.job_id,
            target=job.target,
            project_root=root,
            python=python,
            entrypoint=entrypoint,
            cwd=root,
        )
