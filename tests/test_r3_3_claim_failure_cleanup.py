from __future__ import annotations

import unittest

from contracts.target import Target
from orchestration.service import OrchestrationService


class _Transport:
    def __init__(self):
        self.failed = []
    def queue(self, target):
        return [{"job_id": 131, "kind": "lyrics"}]
    def claim(self, target):
        return {
            "job_id": 131,
            "kind": "lyrics",
            "paths": {},
            "request": {"lyrics_file": r"H:\EZScore\var\storage\lyrics\lyrics.txt"},
            "song": {},
        }
    def complete(self, target, job_id):
        raise AssertionError("must not complete")
    def fail(self, target, job_id, error):
        self.failed.append((target, job_id, error))


class _Scheduler:
    def __init__(self):
        self.job = None
        self.released = []
    def submit(self, job):
        self.job = job
    def next_ready(self):
        return self.job
    def release(self, job):
        self.released.append(job)


class _Executor:
    def run(self, job, on_output=None, on_progress=None):
        raise RuntimeError(
            r"Cross-root path forbidden for dev: H:\EZScore\var\storage\lyrics\lyrics.txt"
        )


class R33ClaimCleanupTest(unittest.TestCase):
    def test_claimed_job_is_failed_if_planner_or_executor_raises(self):
        service = object.__new__(OrchestrationService)
        service.transport = _Transport()
        service.scheduler = _Scheduler()
        service.executor = _Executor()

        with self.assertRaises(RuntimeError):
            service.run_once(Target.DEV)

        self.assertEqual(len(service.transport.failed), 1)
        target, job_id, error = service.transport.failed[0]
        self.assertEqual(target, Target.DEV)
        self.assertEqual(job_id, 131)
        self.assertIn("orchestration_preflight_or_execution_error", error)
        self.assertEqual(len(service.scheduler.released), 1)


if __name__ == "__main__":
    unittest.main()
