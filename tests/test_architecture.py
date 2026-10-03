from __future__ import annotations

import unittest
from pathlib import Path

from config.loader import load_runtime_config
from contracts.job import JobEnvelope
from contracts.target import Target
from executor.planner import ExecutionPlanner
from scheduler.scheduler import Scheduler
from server_manager.manager import ServerManager


class ArchitectureContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_config()

    def test_prod_accepts_prod_only(self):
        manager = ServerManager(self.config)
        self.assertEqual(manager.view(Target.PROD, "prod").app_env, "prod")
        with self.assertRaises(ValueError):
            manager.view(Target.PROD, "dev")

    def test_dev_accepts_dev_and_prod(self):
        manager = ServerManager(self.config)
        self.assertEqual(manager.view(Target.DEV, "dev").app_env, "dev")
        self.assertEqual(manager.view(Target.DEV, "prod").app_env, "prod")

    def test_analysis_code_follows_target(self):
        planner = ExecutionPlanner(self.config)
        dev = planner.plan(JobEnvelope(1, Target.DEV, "lyrics"))
        prod = planner.plan(JobEnvelope(2, Target.PROD, "lyrics"))
        self.assertEqual(dev.entrypoint, Path(r"H:\EZScore_dev") / r"analysis\worker_entrypoint.py")
        self.assertEqual(prod.entrypoint, Path(r"H:\EZScore") / r"analysis\worker_entrypoint.py")

    def test_cross_root_is_rejected(self):
        planner = ExecutionPlanner(self.config)
        dev_job = JobEnvelope(3, Target.DEV, "stems")
        prod_job = JobEnvelope(4, Target.PROD, "stems")
        with self.assertRaises(RuntimeError):
            planner.validate_external_path(dev_job, Path(r"H:\EZScore\var\storage\x.wav"))
        with self.assertRaises(RuntimeError):
            planner.validate_external_path(prod_job, Path(r"H:\EZScore_dev\var\storage\x.wav"))

    def test_single_gpu_slot(self):
        scheduler = Scheduler(gpu_slots=1)
        a = JobEnvelope(10, Target.DEV, "lyrics", resource_class="gpu")
        b = JobEnvelope(11, Target.PROD, "stems", resource_class="gpu")
        scheduler.submit(a)
        scheduler.submit(b)
        first = scheduler.next_ready()
        self.assertIsNotNone(first)
        self.assertIsNone(scheduler.next_ready())
        scheduler.release(first)
        self.assertIsNotNone(scheduler.next_ready())


if __name__ == "__main__":
    unittest.main()
