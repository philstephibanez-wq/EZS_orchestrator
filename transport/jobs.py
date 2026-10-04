from __future__ import annotations

from contracts.target import Target
from runtime_guard.singleton import ExecutionSingleton
from .targets import TargetRegistry


class JobTransport:
    """Transport only: no scheduling and no business execution.

    The machine-wide execution singleton is acquired immediately before claim
    and held until complete/fail. This prevents two orchestrator processes from
    claiming/executing jobs concurrently on the same machine/GPU.
    """

    def __init__(self, registry: TargetRegistry):
        self.registry = registry
        self._execution_singleton = ExecutionSingleton(
            registry.config.orchestrator_root / "runtime"
        )

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
        # Critical boundary: acquire BEFORE changing server-side job state.
        self._execution_singleton.acquire(target=target.value)

        try:
            data = self.registry.endpoint(target).client().post(
                "/internal/analysis/desktop/jobs/claim", {}
            )
        except Exception:
            self._execution_singleton.release()
            raise

        if not data:
            self._execution_singleton.release()
            return None

        raw_job_id = data.get("job_id") if isinstance(data, dict) else None
        try:
            job_id = int(raw_job_id) if raw_job_id is not None else None
        except (TypeError, ValueError):
            job_id = None

        self._execution_singleton.update_metadata(
            target=target.value,
            job_id=job_id,
        )
        return data

    def progress(self, target: Target, job_id: int, percent: int) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/progress",
            {"progress": int(percent)},
        )

    def complete(self, target: Target, job_id: int) -> None:
        try:
            self.registry.endpoint(target).client().post(
                f"/internal/analysis/desktop/jobs/{job_id}/complete", {}
            )
        finally:
            self._execution_singleton.release()

    def fail(self, target: Target, job_id: int, error: str) -> None:
        try:
            self.registry.endpoint(target).client().post(
                f"/internal/analysis/desktop/jobs/{job_id}/fail",
                {"error": str(error)[:400]},
            )
        finally:
            self._execution_singleton.release()

    def release_execution_singleton(self) -> None:
        """Safety valve for orchestration paths that abort after claim."""
        self._execution_singleton.release()
