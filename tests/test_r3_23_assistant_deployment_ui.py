from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
MANAGER = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class R323AssistantDeploymentUiContract(unittest.TestCase):
    def test_assistant_deploy_button_present(self):
        self.assertIn('id="assistantDeploy"', WEB)
        self.assertIn("Déployer assistant", WEB)
        self.assertIn('id="assistantSourceCommit"', WEB)
        self.assertIn('id="assistantDeployedCommit"', WEB)
        self.assertIn('id="assistantDeployState"', WEB)

    def test_ui_has_status_and_apply_routes(self):
        self.assertIn('"/api/assistant/deployment/status"', WEB)
        self.assertIn('"/api/assistant/deployment/apply"', WEB)
        self.assertIn("assistant_deployment_status(self)", WEB)
        self.assertIn("assistant_deployment_apply(self)", WEB)

    def test_status_compares_source_and_deployed_commit(self):
        self.assertIn("def deployment_status(plan: DeployPlan)", MANAGER)
        self.assertIn('"UP_TO_DATE"', MANAGER)
        self.assertIn('"UPDATE_AVAILABLE"', MANAGER)
        self.assertIn('"NOT_DEPLOYED"', MANAGER)
        self.assertIn('"UNREACHABLE"', MANAGER)
        self.assertIn("DEPLOYED_COMMIT.txt", MANAGER)

    def test_deploy_uses_existing_orchestrator_manager(self):
        self.assertIn("deploy as deploy_assistant_node", WEB)
        self.assertIn("result = deploy_assistant_node(plan)", WEB)

    def test_no_distributed_claim_or_scientific_execution_added(self):
        self.assertNotIn('data-action="assistant-run"', WEB)
        self.assertNotIn('data-action="assistant-claim"', WEB)
        self.assertNotIn("/distributed/jobs/claim", WEB)
        self.assertNotIn("distributed-probe", MANAGER)
        self.assertNotIn("distributed-watch", MANAGER)

    def test_no_three_second_ssh_poll(self):
        self.assertIn("refreshAssistantDeployment();setInterval(refresh,3000)", WEB)
        self.assertNotIn("setInterval(refreshAssistantDeployment,3000)", WEB)


if __name__ == "__main__":
    unittest.main()
