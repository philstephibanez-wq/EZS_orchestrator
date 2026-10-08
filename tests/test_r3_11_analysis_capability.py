from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from capability.publisher import AnalysisCapabilityPublisher
from contracts.target import Target
from service.runner import targets_for_scope


class R311AnalysisCapabilityTest(unittest.TestCase):
    def test_all_scope_contains_all_targets(self):
        self.assertEqual(
            targets_for_scope(None),
            (Target.DEV, Target.PROD, Target.LAB),
        )
        self.assertEqual(targets_for_scope(Target.DEV), (Target.DEV,))
        self.assertEqual(targets_for_scope(Target.PROD), (Target.PROD,))
        self.assertEqual(targets_for_scope(Target.LAB), (Target.LAB,))

    def test_capability_is_target_owned(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dev = root / "EZScore_dev"
            prod = root / "EZScore"
            config = SimpleNamespace(
                dev=SimpleNamespace(root=dev),
                prod=SimpleNamespace(root=prod),
            )
            publisher = AnalysisCapabilityPublisher(config)

            publisher.publish(
                Target.DEV,
                available=True,
                state="idle",
                service_scope="all",
                queued=0,
            )
            publisher.publish(
                Target.PROD,
                available=False,
                state="transport_error",
                service_scope="all",
                error="test",
            )

            dev_path = (
                dev / "var" / "runtime" / "orchestrator" / "analysis-capability.json"
            )
            prod_path = (
                prod / "var" / "runtime" / "orchestrator" / "analysis-capability.json"
            )
            self.assertTrue(dev_path.is_file())
            self.assertTrue(prod_path.is_file())

            dev_data = json.loads(dev_path.read_text(encoding="utf-8"))
            prod_data = json.loads(prod_path.read_text(encoding="utf-8"))
            self.assertEqual(dev_data["target"], "dev")
            self.assertTrue(dev_data["available"])
            self.assertEqual(prod_data["target"], "prod")
            self.assertFalse(prod_data["available"])
            self.assertNotEqual(dev_path, prod_path)


if __name__ == "__main__":
    unittest.main()
