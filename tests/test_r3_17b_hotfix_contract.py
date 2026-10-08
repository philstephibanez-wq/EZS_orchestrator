from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from contracts.target import Target
from executor.planner import ExecutionPlanner


class R317BHotfixContractTest(unittest.TestCase):
    @staticmethod
    def _legacy_config(root:Path):
        dev=root/"EZScore_dev"
        prod=root/"EZScore"
        return SimpleNamespace(
            dev=SimpleNamespace(root=dev),
            prod=SimpleNamespace(root=prod),
            dev_analysis_python=dev/".venv-py313"/"Scripts"/"python.exe",
            prod_analysis_python=prod/".venv-py313"/"Scripts"/"python.exe",
            analysis_entrypoint=Path("analysis/worker_entrypoint.py"),
            analysis_python_for=lambda target: (
                dev/".venv-py313"/"Scripts"/"python.exe"
                if target is Target.DEV
                else prod/".venv-py313"/"Scripts"/"python.exe"
            ),
        )

    @staticmethod
    def _job(target):
        class Job:
            job_id=1
            payload={}
            paths={}
            request={}
            song={}
            def validate(self): pass
        j=Job()
        j.target=target
        return j

    def test_legacy_dev_fixture_without_lab_attribute_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self._legacy_config(Path(td))
            plan=ExecutionPlanner(cfg).plan(self._job(Target.DEV))
            self.assertEqual(plan.project_root,cfg.dev.root)

    def test_legacy_prod_fixture_without_lab_attribute_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self._legacy_config(Path(td))
            plan=ExecutionPlanner(cfg).plan(self._job(Target.PROD))
            self.assertEqual(plan.project_root,cfg.prod.root)

    def test_dev_still_rejects_prod_python(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self._legacy_config(Path(td))
            cfg.analysis_python_for=lambda target: cfg.prod_analysis_python
            with self.assertRaisesRegex(RuntimeError,"Cross-root analysis Python"):
                ExecutionPlanner(cfg).plan(self._job(Target.DEV))

if __name__=="__main__":
    unittest.main()
