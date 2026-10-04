from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .target import Target

JOB_PROTOCOL = "ezscore.analysis-job.v2"


@dataclass(frozen=True, slots=True)
class JobEnvelope:
    job_id: int
    target: Target
    kind: str
    resource_class: str = "gpu"
    priority: int = 50
    song_id: int | None = None
    paths: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    song: dict[str, Any] = field(default_factory=dict)
    protocol: str = JOB_PROTOCOL

    # Temporary R3.1 compatibility bridge for R1/R2 callers/tests.
    # It is NOT serialized into the v2 execution envelope and is NOT
    # authoritative for business execution. It is only carried so that
    # legacy callers can still express nested paths for guard validation.
    payload: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.protocol != JOB_PROTOCOL:
            raise ValueError(
                f"Unsupported job protocol: {self.protocol}; expected={JOB_PROTOCOL}"
            )
        if self.job_id <= 0:
            raise ValueError("job_id must be positive")
        if not self.kind.strip():
            raise ValueError("kind is required")
        if self.resource_class not in {"gpu", "cpu"}:
            raise ValueError(f"unsupported resource_class: {self.resource_class}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "protocol": self.protocol,
            "job_id": self.job_id,
            "target": self.target.value,
            "kind": self.kind,
            "song_id": self.song_id,
            "resource_class": self.resource_class,
            "priority": self.priority,
            "paths": self.paths,
            "request": self.request,
            "song": self.song,
        }

    @classmethod
    def from_api(cls, raw: dict[str, Any], target: Target) -> "JobEnvelope":
        protocol = str(raw.get("protocol") or JOB_PROTOCOL)
        if protocol != JOB_PROTOCOL:
            raise ValueError(
                f"Unsupported API job protocol: {protocol}; expected={JOB_PROTOCOL}"
            )
        return cls(
            job_id=int(raw["job_id"]),
            target=target,
            kind=str(raw.get("kind") or ""),
            resource_class=str(raw.get("resource_class") or "gpu"),
            priority=int(raw.get("priority") or 50),
            song_id=int(raw["song_id"]) if raw.get("song_id") is not None else None,
            paths=dict(raw.get("paths") or {}),
            request=dict(raw.get("request") or {}),
            song=dict(raw.get("song") or {}),
            protocol=protocol,
        )
