from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field

from contracts.job import JobEnvelope


@dataclass(order=True)
class _Queued:
    sort_key: tuple[int, int]
    job: JobEnvelope = field(compare=False)


class Scheduler:
    """Pure resource scheduler.

    It has no HTTP knowledge and no musical-analysis knowledge.
    """

    def __init__(self, gpu_slots: int = 1):
        if gpu_slots < 1:
            raise ValueError("gpu_slots must be >= 1")
        self.gpu_slots = gpu_slots
        self._gpu_in_use = 0
        self._counter = itertools.count()
        self._queue: list[_Queued] = []

    def submit(self, job: JobEnvelope) -> None:
        job.validate()
        heapq.heappush(
            self._queue,
            _Queued((-job.priority, next(self._counter)), job),
        )

    def next_ready(self) -> JobEnvelope | None:
        if not self._queue:
            return None
        skipped: list[_Queued] = []
        selected = None
        while self._queue:
            item = heapq.heappop(self._queue)
            if item.job.resource_class == "gpu" and self._gpu_in_use >= self.gpu_slots:
                skipped.append(item)
                continue
            selected = item.job
            if selected.resource_class == "gpu":
                self._gpu_in_use += 1
            break
        for item in skipped:
            heapq.heappush(self._queue, item)
        return selected

    def release(self, job: JobEnvelope) -> None:
        if job.resource_class == "gpu":
            if self._gpu_in_use <= 0:
                raise RuntimeError("GPU release without active slot")
            self._gpu_in_use -= 1

    @property
    def queued(self) -> int:
        return len(self._queue)

    @property
    def gpu_in_use(self) -> int:
        return self._gpu_in_use
