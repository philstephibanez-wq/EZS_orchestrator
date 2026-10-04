from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from contracts.target import Target
from executor.planner import ExecutionPlan, ExecutionPlanner
from executor.runner import JobExecutor


class R34aRuntimeBoundaryTest(unittest.TestCase):
    def test_planner_checks_ownership_not_runtime_existence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dev = root / "EZScore_dev"
            prod = root / "EZScore"
            dev.mkdir()
            prod.mkdir()

            missing_dev_python = (
                dev / ".venv-py313" / "Scripts" / "python.exe"
            )

            cfg = SimpleNamespace(
                dev=SimpleNamespace(root=dev),
                prod=SimpleNamespace(root=prod),
                dev_analysis_python=missing_dev_python,
                prod_analysis_python=prod / ".venv-py313" / "Scripts" / "python.exe",
                analysis_entrypoint=Path("analysis/worker_entrypoint.py"),
                analysis_python_for=lambda target: (
                    missing_dev_python
                    if target is Target.DEV
                    else prod / ".venv-py313" / "Scripts" / "python.exe"
                ),
            )

            class Job:
                job_id = 1
                target = Target.DEV
                payload = {}
                paths = {}
                request = {}
                song = {}
                def validate(self): pass

            plan = ExecutionPlanner(cfg).plan(Job())
            self.assertEqual(plan.python, missing_dev_python)

    def test_executor_rejects_missing_python_before_spawn(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = ExecutionPlan(
                job_id=1,
                target=Target.DEV,
                project_root=root,
                python=root / "missing-python.exe",
                entrypoint=root / "analysis" / "worker_entrypoint.py",
                cwd=root,
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "analysis_python_missing:dev:",
            ):
                JobExecutor._validate_runtime_files(plan)


if __name__ == "__main__":
    unittest.main()
