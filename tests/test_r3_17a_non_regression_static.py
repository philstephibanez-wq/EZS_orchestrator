from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LabR317AStaticNonRegressionTest(unittest.TestCase):
    def test_runtime_dev_prod_values_unchanged(self):
        data = json.loads((ROOT / "config" / "runtime.json").read_text(encoding="utf-8"))
        self.assertEqual(data["servers"]["dev"]["root"], r"H:\EZScore_dev")
        self.assertEqual(data["servers"]["dev"]["backend_port"], 8602)
        self.assertEqual(data["servers"]["dev"]["public_port"], 8502)
        self.assertEqual(
            data["servers"]["dev"]["analysis_python"],
            r"H:\EZScore_dev\.venv-py313\Scripts\python.exe",
        )
        self.assertEqual(data["servers"]["prod"]["root"], r"H:\EZScore")
        self.assertEqual(data["servers"]["prod"]["backend_port"], 8511)
        self.assertEqual(data["servers"]["prod"]["gateway_port"], 8510)
        self.assertEqual(data["servers"]["prod"]["public_port"], 8501)
        self.assertEqual(
            data["servers"]["prod"]["analysis_python"],
            r"H:\EZScore\.venv-py313\Scripts\python.exe",
        )
        self.assertEqual(data["transport"]["dev_backend_url"], "http://127.0.0.1:8602")
        self.assertEqual(data["transport"]["prod_backend_url"], "http://127.0.0.1:8511")

    def test_server_lifecycle_cli_still_only_dev_prod(self):
        source = (ROOT / "control_center" / "cli.py").read_text(encoding="utf-8")
        self.assertIn('p.add_argument("target", choices=("dev", "prod"))', source)
        self.assertNotIn('p.add_argument("target", choices=("dev", "prod", "lab"))', source)

    def test_gpu_singleton_name_unchanged(self):
        source = (ROOT / "runtime_guard" / "singleton.py").read_text(encoding="utf-8")
        self.assertIn(r'WINDOWS_MUTEX_NAME = r"Global\EZS_orchestrator_analysis_executor_v1"', source)

    def test_prod_deployment_contract_untouched(self):
        source = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
        for action in (
            "prod-start",
            "prod-stop",
            "prod-restart",
            "prod-maintenance-on",
            "prod-maintenance-off",
        ):
            self.assertIn(action, source)


if __name__ == "__main__":
    unittest.main()
