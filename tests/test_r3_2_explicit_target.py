from __future__ import annotations

import unittest

from contracts.target import Target
from orchestration.service import OrchestrationService


class _FakeTransport:
    def __init__(self):
        self.queues = {
            Target.DEV: [{"job_id": 200, "kind": "lyrics"}],
            Target.PROD: [{"job_id": 131, "kind": "lyrics"}],
        }
        self.claimed_targets: list[Target] = []

    def queue(self, target):
        return self.queues[target]

    def claim(self, target):
        self.claimed_targets.append(target)
        return dict(self.queues[target][0])

    def complete(self, target, job_id):
        pass

    def fail(self, target, job_id, error):
        pass


class _FakeExecutor:
    class R:
        returncode = 0
        stdout_tail = ()

    def run(self, job, on_output=None):
        return self.R()


class _FakeScheduler:
    def __init__(self):
        self.job = None

    def submit(self, job):
        self.job = job

    def next_ready(self):
        return self.job

    def release(self, job):
        pass


class R32ExplicitTargetContractTest(unittest.TestCase):
    def make_service(self):
        service = object.__new__(OrchestrationService)
        service.transport = _FakeTransport()
        service.executor = _FakeExecutor()
        service.scheduler = _FakeScheduler()
        return service

    def test_dev_run_never_claims_prod(self):
        service = self.make_service()
        outcome = service.run_once(Target.DEV)
        self.assertEqual(outcome.target, Target.DEV)
        self.assertEqual(service.transport.claimed_targets, [Target.DEV])

    def test_prod_run_never_claims_dev(self):
        service = self.make_service()
        outcome = service.run_once(Target.PROD)
        self.assertEqual(outcome.target, Target.PROD)
        self.assertEqual(service.transport.claimed_targets, [Target.PROD])


if __name__ == "__main__":
    unittest.main()
