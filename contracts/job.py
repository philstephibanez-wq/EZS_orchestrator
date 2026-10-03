from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .target import Target

JOB_PROTOCOL = "ezscore.job.v1"


@dataclass(frozen=True, slots=True)
class JobEnvelope:
    job_id: int
    target: Target
    kind: str
    resource_class: str = "gpu"
    priority: int = 50
    payload: dict[str, Any] = field(default_factory=dict)
    protocol: str = JOB_PROTOCOL

    def validate(self) -> None:
        if self.protocol != JOB_PROTOCOL:
            raise ValueError(f"Unsupported job protocol: {self.protocol}")
        if self.job_id <= 0:
            raise ValueError("job_id must be positive")
        if not self.kind.strip():
            raise ValueError("kind is required")
        if self.resource_class not in {"gpu", "cpu"}:
            raise ValueError(f"unsupported resource_class: {self.resource_class}")
