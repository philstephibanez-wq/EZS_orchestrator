from __future__ import annotations

from contracts.target import Target
from .targets import TargetRegistry


class JobTransport:
    """Transport only: no scheduling and no business execution."""

    def __init__(self, registry: TargetRegistry):
        self.registry = registry

    def queue(self, target: Target) -> list[dict]:
        endpoint = self.registry.endpoint(target)
        data = endpoint.client().get("/internal/analysis/desktop/jobs/queue")
        return list((data or {}).get("jobs") or [])

    def hello(self, target: Target, payload: dict) -> dict:
        return self.registry.endpoint(target).client().post(
            "/internal/analysis/desktop/hello", payload
        )

    def heartbeat(self, target: Target, payload: dict) -> dict:
        return self.registry.endpoint(target).client().post(
            "/internal/analysis/desktop/heartbeat", payload
        )

    def claim(self, target: Target) -> dict | None:
        data = self.registry.endpoint(target).client().post(
            "/internal/analysis/desktop/jobs/claim", {}
        )
        return data or None

    def progress(self, target: Target, job_id: int, percent: int) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/progress",
            {"progress": int(percent)},
        )

    def complete(self, target: Target, job_id: int) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/complete", {}
        )

    def fail(self, target: Target, job_id: int, error: str) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/fail",
            {"error": str(error)[:400]},
        )
