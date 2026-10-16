from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class V12fAssistantDeploymentCleanupContract(unittest.TestCase):
    def test_previous_is_kept_until_live_runtime_validation(self):
        move_current = DEPLOY.index(
            "[System.IO.Directory]::Move($remoteRoot, $previous)"
        )
        staged = DEPLOY.index("EZS_ASSISTANT_REMOTE_DEPLOY_STAGED_OK")
        finalize = DEPLOY.index("def finalize_deployment(plan: DeployPlan)")
        cleanup = DEPLOY.index(
            "Remove-Item -LiteralPath $legacy -Recurse -Force",
            finalize,
        )
        self.assertLess(move_current, staged)
        self.assertLess(staged, finalize)
        self.assertLess(finalize, cleanup)

    def test_finalize_requires_web_workers_and_runtime_state(self):
        self.assertIn("assistant_finalize_web_not_running", DEPLOY)
        self.assertIn("assistant_finalize_distributed_not_singleton", DEPLOY)
        self.assertIn("assistant_finalize_profile_not_singleton", DEPLOY)
        self.assertIn("assistant_finalize_state_missing", DEPLOY)
        self.assertIn("assistant_finalize_web_runtime_missing", DEPLOY)

    def test_failed_live_validation_has_rollback(self):
        self.assertIn("def rollback_deployment(plan: DeployPlan)", DEPLOY)
        self.assertIn("assistant_rollback_no_previous_recovered_current_root", DEPLOY)
        self.assertIn("EZS_ASSISTANT_REMOTE_DEPLOY_ROLLBACK_OK", DEPLOY)

    def test_runtime_is_staged_inside_single_root_clone(self):
        self.assertIn(
            'DEFAULT_REMOTE_HOST_REPO = r"C:\\EZStudioLab_assistant\\runtime"',
            DEPLOY,
        )
        self.assertIn("$runtimeStaging = Join-Path $staging 'runtime'", DEPLOY)
        self.assertIn(
            "Expand-Archive -LiteralPath $archive -DestinationPath $runtimeStaging -Force",
            DEPLOY,
        )

    def test_persistent_state_is_migrated_inside_single_root(self):
        self.assertIn("$stateTarget = Join-Path $runtimeRoot 'state'", DEPLOY)
        self.assertIn("$legacyStateRuntime", DEPLOY)

        # Validate generated PowerShell rather than Python source escaping.
        from assistant_deployment.manager import DeployPlan, _remote_script

        plan = DeployPlan(
            source=r"H:\\EZStudioLab_assistant",
            source_commit="a" * 40,
            parent_gitlink_commit="a" * 40,
            node="test@example",
            remote_root=r"C:\\EZStudioLab_assistant",
            remote_host_repo=r"C:\\EZStudioLab_assistant\\runtime",
        )
        rendered = _remote_script(plan, "runtime.zip")
        self.assertIn(
            "$persistentSource = Join-Path (Join-Path $previous 'runtime') $runtimeName",
            rendered,
        )
        self.assertIn("'state'", rendered)


if __name__ == "__main__":
    unittest.main()
