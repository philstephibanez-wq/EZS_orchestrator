from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class R343AssistantPostDeployRuntimeGateContract(unittest.TestCase):
    def test_deploy_starts_runtime_before_finalize(self):
        method = WEB.index("def assistant_deployment_apply(self) -> dict:")
        start = WEB.index("self.assistant_supervision.start()", method)
        finalize = WEB.index("finalize_assistant_deployment(plan)", method)
        self.assertLess(start, finalize)
        self.assertIn("assistant_post_deploy_runtime_not_running", WEB[method:finalize])

    def test_failed_post_deploy_validation_rolls_back(self):
        self.assertIn("rollback_assistant_deployment(plan)", WEB)
        self.assertIn("assistant_post_deploy_validation_failed", WEB)

    def test_inventory_cannot_promote_stopped_runtime(self):
        method = WEB.index("def assistant_supervision_status(self) -> dict:")
        end = WEB.index("def assistant_logs", method)
        body = WEB[method:end]
        self.assertIn('remote_state == "RUNNING"', body)
        self.assertIn('remote_state == "DEGRADED"', body)
        self.assertIn('remote_state == "STOPPED"', body)
        self.assertNotIn("elif online:", body)

    def test_ui_buttons_follow_full_runtime_state(self):
        self.assertIn('const running=state==="ONLINE"||state==="BUSY";', WEB)
        self.assertIn('const degraded=state==="DEGRADED";', WEB)
        self.assertIn('const active=running||degraded;', WEB)
        self.assertIn('DEGRADED:"DÉGRADÉ"', WEB)

    def test_deploy_refreshes_runtime_status(self):
        marker = '$("assistantDeploy").addEventListener("click",async()=>{'
        start = WEB.index(marker)
        end = WEB.index("document.querySelectorAll(", start)
        handler = WEB[start:end]
        self.assertIn("await refreshAssistantSupervision();", handler)

    def test_cleanup_is_gated_by_live_runtime(self):
        self.assertIn("def finalize_deployment(plan: DeployPlan)", DEPLOY)
        self.assertIn("assistant_finalize_web_not_running", DEPLOY)
        self.assertIn("assistant_finalize_distributed_not_singleton", DEPLOY)
        self.assertIn("assistant_finalize_profile_not_singleton", DEPLOY)


if __name__ == "__main__":
    unittest.main()
