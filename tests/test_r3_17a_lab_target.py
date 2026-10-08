from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from capability.publisher import AnalysisCapabilityPublisher
from config.loader import load_runtime_config
from contracts.target import Target
from executor.planner import ExecutionPlanner
from orchestration.service import OrchestrationService
from service.runner import targets_for_scope


class _FakeTransport:
    def __init__(self):
        self.queues = {
            Target.DEV: [{"job_id": 11, "kind": "stems"}],
            Target.PROD: [{"job_id": 12, "kind": "lyrics"}],
            Target.LAB: [{"job_id": 13, "kind": "stems"}],
        }
        self.claimed_targets = []

    def queue(self, target):
        return self.queues[target]

    def claim(self, target):
        self.claimed_targets.append(target)
        row = dict(self.queues[target][0])
        row.update({
            "protocol": "ezscore.analysis-job.v2",
            "resource_class": "gpu",
            "priority": 50,
            "paths": {},
            "request": {},
            "song": {},
        })
        return row

    def progress(self, *args, **kwargs): pass
    def complete(self, *args, **kwargs): pass
    def fail(self, *args, **kwargs): pass


class _FakeExecutor:
    class R:
        returncode = 0
        stdout_tail = ()

    def run(self, job, on_output=None, on_progress=None):
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


class LabTargetR317AContractTest(unittest.TestCase):
    def test_target_enum(self):
        self.assertEqual(Target.LAB.value, "lab")

    def test_scope_all_is_dev_prod_lab(self):
        self.assertEqual(
            targets_for_scope(None),
            (Target.DEV, Target.PROD, Target.LAB),
        )

    def test_runtime_config_preserves_dev_prod_and_adds_lab(self):
        cfg = load_runtime_config()
        self.assertEqual(str(cfg.dev.root), r"H:\EZScore_dev")
        self.assertEqual(str(cfg.prod.root), r"H:\EZScore")
        self.assertIsNotNone(cfg.lab)
        self.assertEqual(str(cfg.lab.root), r"H:\EZStudio_lab")
        self.assertEqual(cfg.dev_backend_url, "http://127.0.0.1:8602")
        self.assertEqual(cfg.prod_backend_url, "http://127.0.0.1:8511")
        self.assertEqual(cfg.lab_backend_url, "http://127.0.0.1:8701")
        self.assertEqual(
            str(cfg.dev_analysis_python),
            r"H:\EZScore_dev\.venv-py313\Scripts\python.exe",
        )
        self.assertEqual(
            str(cfg.prod_analysis_python),
            r"H:\EZScore\.venv-py313\Scripts\python.exe",
        )
        self.assertEqual(
            str(cfg.lab_analysis_python),
            r"H:\Python\pythoncore-3.14-64\python.exe",
        )

    def _planner_config(self, root: Path):
        dev = root / "EZScore_dev"
        prod = root / "EZScore"
        lab = root / "EZStudio_lab"
        outside = root / "Python" / "python.exe"
        return SimpleNamespace(
            dev=SimpleNamespace(root=dev),
            prod=SimpleNamespace(root=prod),
            lab=SimpleNamespace(root=lab),
            dev_analysis_python=dev / ".venv" / "python.exe",
            prod_analysis_python=prod / ".venv" / "python.exe",
            lab_analysis_python=outside,
            analysis_entrypoint=Path("analysis/worker_entrypoint.py"),
            analysis_python_for=lambda target: (
                dev / ".venv" / "python.exe"
                if target is Target.DEV
                else prod / ".venv" / "python.exe"
                if target is Target.PROD
                else outside
            ),
        )

    @staticmethod
    def _job(target):
        class Job:
            job_id = 1
            payload = {}
            paths = {}
            request = {}
            song = {}
            def validate(self): pass
        job = Job()
        job.target = target
        return job

    def test_cross_root_isolation_three_targets(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._planner_config(Path(td))
            planner = ExecutionPlanner(cfg)

            dev = self._job(Target.DEV)
            prod = self._job(Target.PROD)
            lab = self._job(Target.LAB)

            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(dev, cfg.prod.root / "x")
            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(dev, cfg.lab.root / "x")

            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(prod, cfg.dev.root / "x")
            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(prod, cfg.lab.root / "x")

            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(lab, cfg.dev.root / "x")
            with self.assertRaisesRegex(RuntimeError, "Cross-root path forbidden"):
                planner.validate_external_path(lab, cfg.prod.root / "x")

    def test_dev_prod_python_ownership_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._planner_config(Path(td))
            planner = ExecutionPlanner(cfg)

            dev_plan = planner.plan(self._job(Target.DEV))
            prod_plan = planner.plan(self._job(Target.PROD))
            self.assertTrue(planner._is_under(dev_plan.python, cfg.dev.root))
            self.assertTrue(planner._is_under(prod_plan.python, cfg.prod.root))

    def test_lab_allows_only_configured_external_python(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._planner_config(Path(td))
            planner = ExecutionPlanner(cfg)

            plan = planner.plan(self._job(Target.LAB))
            self.assertEqual(plan.python, cfg.lab_analysis_python)
            self.assertEqual(plan.project_root, cfg.lab.root)

            original = cfg.analysis_python_for
            cfg.analysis_python_for = lambda target: Path(td) / "OtherPython" / "python.exe"
            with self.assertRaisesRegex(RuntimeError, "must match configured executable"):
                planner.plan(self._job(Target.LAB))
            cfg.analysis_python_for = original

    def test_explicit_target_claims_lab_only(self):
        service = object.__new__(OrchestrationService)
        service.transport = _FakeTransport()
        service.executor = _FakeExecutor()
        service.scheduler = _FakeScheduler()

        outcome = service.run_once(Target.LAB)
        self.assertEqual(outcome.target, Target.LAB)
        self.assertEqual(service.transport.claimed_targets, [Target.LAB])

    def test_capability_paths_are_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = SimpleNamespace(
                dev=SimpleNamespace(root=root / "dev"),
                prod=SimpleNamespace(root=root / "prod"),
                lab=SimpleNamespace(root=root / "lab"),
            )
            publisher = AnalysisCapabilityPublisher(cfg)
            paths = {
                publisher.path_for(Target.DEV),
                publisher.path_for(Target.PROD),
                publisher.path_for(Target.LAB),
            }
            self.assertEqual(len(paths), 3)


if __name__ == "__main__":
    unittest.main()
