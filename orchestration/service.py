from __future__ import annotations

import json

from dataclasses import dataclass
from typing import Callable

from config.loader import RuntimeConfig
from contracts.job import JobEnvelope
from contracts.target import Target
from executor.runner import JobExecutor, ExecutionResult
from scheduler.scheduler import Scheduler
from transport.jobs import JobTransport
from transport.targets import TargetRegistry


@dataclass(frozen=True, slots=True)
class RunOutcome:
    target: Target
    job_id: int
    returncode: int


class OrchestrationService:
    """Single-target orchestration.

    R3.3 guarantee:
    once a job has been claimed, any orchestration/planner/executor exception
    is reported to the target API so the job cannot remain silently stuck in
    `running`.

    Queue candidates are intentionally minimal. Full path validation can only
    happen after claim because the claim response carries the complete envelope.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.transport = JobTransport(TargetRegistry(config))
        self.scheduler = Scheduler(gpu_slots=config.gpu_slots)
        self.executor = JobExecutor(config)

    def candidate(self, target: Target) -> JobEnvelope | None:
        queue = self.transport.queue(target)
        if not queue:
            return None
        return JobEnvelope.from_api(queue[0], target)

    def run_once(
        self,
        target: Target,
        *,
        on_output: Callable[[str], None] | None = None,
    ) -> RunOutcome | None:
        selected = self.candidate(target)
        if selected is None:
            return None

        self.scheduler.submit(selected)
        reserved = self.scheduler.next_ready()
        if reserved is None:
            return None
        if reserved.target is not target:
            self.scheduler.release(reserved)
            raise RuntimeError(
                f"scheduler_target_mismatch:requested={target.value};"
                f"selected={reserved.target.value}"
            )

        claimed: JobEnvelope | None = None

        try:
            raw_claimed = self.transport.claim(target)
            if not raw_claimed:
                return None

            claimed = JobEnvelope.from_api(raw_claimed, target)

            if claimed.target is not target:
                raise RuntimeError(
                    f"claim_target_mismatch:requested={target.value};"
                    f"claimed={claimed.target.value}"
                )

            if claimed.job_id != selected.job_id:
                raise RuntimeError(
                    "queue_claim_contract_mismatch:"
                    f"selected={selected.job_id};claimed={claimed.job_id}"
                )

            if on_output is not None:
                song_title = (
                    claimed.song.get("title")
                    or claimed.song.get("name")
                    or claimed.request.get("title")
                )
                on_output(json.dumps({
                    "event": "job_meta",
                    "job_id": claimed.job_id,
                    "kind": claimed.kind,
                    "song_id": claimed.song_id,
                    "song_title": song_title,
                }, ensure_ascii=False))

            # Executor performs Planner validation before spawning the subprocess.
            # Any exception here is handled below and converted to target fail.
            def publish_progress(percent: int) -> None:
                self.transport.progress(target, claimed.job_id, percent)
                if on_output is not None:
                    on_output(json.dumps({
                        "event": "job_progress",
                        "job_id": claimed.job_id,
                        "kind": claimed.kind,
                        "progress": int(percent),
                    }, ensure_ascii=False))

            result: ExecutionResult = self.executor.run(
                claimed,
                on_output=on_output,
                on_progress=publish_progress,
                should_cancel=lambda: self.transport.cancel_requested(
                    target, claimed.job_id
                ),
            )

            if result.cancelled:
                self.transport.cancelled(target, claimed.job_id)
                if on_output is not None:
                    on_output(json.dumps({
                        "event": "job_cancelled",
                        "job_id": claimed.job_id,
                        "kind": claimed.kind,
                    }, ensure_ascii=False))
                return RunOutcome(
                    target=target,
                    job_id=claimed.job_id,
                    returncode=0,
                )

            if result.returncode == 0:
                try:
                    self.transport.complete(target, claimed.job_id)
                except Exception as finalize_exc:
                    if on_output is not None:
                        on_output(json.dumps({
                            "event": "job_finalize_error",
                            "job_id": claimed.job_id,
                            "kind": claimed.kind,
                            "analysis_returncode": 0,
                            "finalize_status": "error",
                            "error": f"{type(finalize_exc).__name__}:{finalize_exc}",
                        }, ensure_ascii=False))
                    return RunOutcome(target=target, job_id=claimed.job_id, returncode=75)
            else:
                detail = " | ".join(result.stdout_tail[-6:])
                error = (
                    f"analysis_entrypoint_exit_{result.returncode}"
                    + (f": {detail}" if detail else "")
                )
                self.transport.fail(target, claimed.job_id, error)

            return RunOutcome(
                target=target,
                job_id=claimed.job_id,
                returncode=result.returncode,
            )

        except Exception as exc:
            if claimed is not None:
                # Best effort fail-closed cleanup. Never mask the original
                # orchestration exception if the reporting request also fails.
                try:
                    self.transport.fail(
                        target,
                        claimed.job_id,
                        f"orchestration_preflight_or_execution_error:{type(exc).__name__}:{exc}",
                    )
                except Exception:
                    pass
            raise

        finally:
            self.scheduler.release(reserved)
