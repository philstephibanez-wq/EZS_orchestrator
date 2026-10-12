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

    def test_assistant_deployment_audit_is_not_logically_cleared(self):
        self.assertIn("PROTECTED_AUDIT_LOGS", LOG_TOOLS)
        self.assertIn('"logs/assistant-deployment.log"', LOG_TOOLS)
        self.assertIn("if self._relative_key(path) in self.PROTECTED_AUDIT_LOGS:", LOG_TOOLS)

    def test_clear_button_is_disabled_for_both_deployment_audits(self):
        self.assertIn('currentLog==="deployments"||currentLog==="assistant_deployment"', WEB)

    def test_no_scientific_execution_added(self):
        self.assertNotIn("distributed-probe", MANAGER)
        self.assertNotIn("distributed-watch", MANAGER)


if __name__ == "__main__":
    unittest.main()
