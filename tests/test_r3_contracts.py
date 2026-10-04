from __future__ import annotations

import ast
import unittest
from pathlib import Path

from config.loader import load_runtime_config
from contracts.job import JOB_PROTOCOL, JobEnvelope
from contracts.target import Target
from executor.planner import ExecutionPlanner


class R3ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.config = load_runtime_config()

    def test_protocol_v2(self):
        self.assertEqual(JOB_PROTOCOL, "ezscore.analysis-job.v2")

    def test_dev_and_prod_entrypoints_are_checkout_owned(self):
        planner = ExecutionPlanner(self.config)
        dev = planner.plan(JobEnvelope(1, Target.DEV, "stems"))
        prod = planner.plan(JobEnvelope(2, Target.PROD, "stems"))
        self.assertEqual(
            dev.entrypoint,
            Path(r"H:\EZScore_dev") / r"analysis\worker_entrypoint.py",
        )
        self.assertEqual(
            prod.entrypoint,
            Path(r"H:\EZScore") / r"analysis\worker_entrypoint.py",
        )

    def test_executor_has_no_business_script_names(self):
        text = (self.root / "executor" / "runner.py").read_text(
            encoding="utf-8"
        ).lower()
        for forbidden in (
            "stems_only.py",
            "chord_timeline_analysis.py",
            "lyrics_timeline_analysis.py",
            "build_playback_proxies.py",
            "whisper",
            "bs_roformer",
        ):
            self.assertNotIn(forbidden, text)

    def test_scheduler_still_has_no_transport_or_analysis_imports(self):
        path = self.root / "scheduler" / "scheduler.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        for module in modules:
            self.assertFalse(
                module.startswith(("transport", "executor", "analysis")),
                module,
            )

    def test_api_adapter_rejects_unknown_protocol(self):
        with self.assertRaises(ValueError):
            JobEnvelope.from_api(
                {
                    "protocol": "ezscore.analysis-job.v999",
                    "job_id": 9,
                    "kind": "stems",
                },
                Target.DEV,
            )


if __name__ == "__main__":
    unittest.main()
