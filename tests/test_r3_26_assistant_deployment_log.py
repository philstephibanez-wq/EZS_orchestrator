from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
MANAGER = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
LOG_TOOLS = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")


class R326AssistantDeploymentLogContract(unittest.TestCase):
    def test_assistant_deployment_has_dedicated_audit_log(self):
        self.assertIn("ASSISTANT_DEPLOYMENT_LOG =", MANAGER)
        self.assertIn('"assistant-deployment.log"', MANAGER)
        self.assertIn("def _audit_deployment(", MANAGER)
        self.assertIn('"START"', MANAGER)
        self.assertIn('"OK"', MANAGER)
        self.assertIn('"FAIL"', MANAGER)

    def test_ui_has_separate_assistant_deployment_tab(self):
        self.assertIn('data-log="assistant_deployment"', WEB)
        self.assertIn(">Déploiement assistant → XPS<", WEB)
        self.assertIn(">Déploiement DEV → PROD<", WEB)
        self.assertIn('"assistant_deployment": self.log_tools.tail(', WEB)

    def test_assistant_deployment_log_is_managed_by_current_log_center(self):
        self.assertIn('"assistant-deployment.log"', MANAGER)
        self.assertIn("def clear_logs(self) -> LogClearResult:", LOG_TOOLS)
        self.assertIn('with path.open("r+b") as handle:', LOG_TOOLS)
        self.assertIn("handle.truncate(0)", LOG_TOOLS)

    def test_clear_button_uses_current_global_physical_clear_contract(self):
        self.assertIn('id="clearLogs"', WEB)
        self.assertIn('action("logs-clear")', WEB)
        self.assertIn("physically truncated", WEB)
        self.assertNotIn('currentLog==="deployments"||currentLog==="assistant_deployment"', WEB)

    def test_no_scientific_execution_added(self):
        self.assertNotIn("distributed-probe", MANAGER)
        self.assertNotIn("distributed-watch", MANAGER)


if __name__ == "__main__":
    unittest.main()
