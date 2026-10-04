from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from contracts.target import Target
from executor.planner import ExecutionPlanner


class R34TargetPythonContractTest(unittest.TestCase):
    def _config(self, root: Path):
        dev = root / "EZScore_dev"
        prod = root / "EZScore"
        dev_python = dev / ".venv-py313" / "Scripts" / "python.exe"
        prod_python = prod / ".venv-py313" / "Scripts" / "python.exe"
        for p in (
            dev_python,
            prod_python,
            dev / "analysis" / "worker_entrypoint.py",
            prod / "analysis" / "worker_entrypoint.py",
        ):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")
        return SimpleNamespace(
            dev=SimpleNamespace(root=dev),
            prod=SimpleNamespace(root=prod),
            dev_analysis_python=dev_python,
            prod_analysis_python=prod_python,
            analysis_entrypoint=Path("analysis/worker_entrypoint.py"),
            analysis_python_for=lambda target: (
                dev_python if target is Target.DEV else prod_python
            ),
        )

    def _job(self, target: Target):
        class Job:
            job_id = 123
            payload = {}
            paths = {}
            request = {}
            song = {}
            def validate(self): pass
        job = Job()
        job.target = target
        return job

    def test_dev_uses_dev_owned_python(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._config(Path(td))
            plan = ExecutionPlanner(cfg).plan(self._job(Target.DEV))
            self.assertEqual(plan.python, cfg.dev_analysis_python)
            self.assertTrue(str(plan.python).startswith(str(cfg.dev.root)))

    def test_prod_uses_prod_owned_python(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._config(Path(td))
            plan = ExecutionPlanner(cfg).plan(self._job(Target.PROD))
            self.assertEqual(plan.python, cfg.prod_analysis_python)
            self.assertTrue(str(plan.python).startswith(str(cfg.prod.root)))

    def test_dev_rejects_prod_python(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = self._config(Path(td))
            cfg.analysis_python_for = lambda target: cfg.prod_analysis_python
            with self.assertRaisesRegex(RuntimeError, "Cross-root analysis Python"):
                ExecutionPlanner(cfg).plan(self._job(Target.DEV))


if __name__ == "__main__":
    unittest.main()
