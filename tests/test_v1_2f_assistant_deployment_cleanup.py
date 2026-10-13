from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class V12fAssistantDeploymentCleanupContract(unittest.TestCase):
    def test_previous_is_removed_only_after_remote_validation(self):
        move_current = DEPLOY.index(
            "Move-Item -LiteralPath $remoteRoot -Destination $previous"
        )
        commit_verify = DEPLOY.index("remote_commit_mismatch:$deployed")
        helper_verify = DEPLOY.index(
            "remote_supervision_helper_missing_after_install"
        )
        cleanup = DEPLOY.index(
            "Remove-Item -LiteralPath $previous -Recurse -Force",
            helper_verify,
        )
        success = DEPLOY.index("EZS_ASSISTANT_REMOTE_DEPLOY_OK", cleanup)

        self.assertLess(move_current, commit_verify)
        self.assertLess(commit_verify, helper_verify)
        self.assertLess(helper_verify, cleanup)
        self.assertLess(cleanup, success)

    def test_previous_is_not_a_persistent_deployment_artifact(self):
        self.assertEqual(
            DEPLOY.count("Move-Item -LiteralPath $remoteRoot -Destination $previous"),
            1,
        )
        self.assertGreaterEqual(
            DEPLOY.count("Remove-Item -LiteralPath $previous -Recurse -Force"),
            2,
        )
        self.assertNotIn(".__previous.", DEPLOY)
        self.assertNotIn(".__backup", DEPLOY)


if __name__ == "__main__":
    unittest.main()
