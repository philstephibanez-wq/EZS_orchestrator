from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
SUPERVISION = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")


class R341AssistantSingleRootRuntimeContract(unittest.TestCase):
    def test_runtime_default_is_inside_assistant_root(self):
        self.assertIn(
            'DEFAULT_REMOTE_HOST_REPO = r"C:\\EZStudioLab_assistant\\runtime"',
            DEPLOY,
        )
        self.assertIn(
            'DEFAULT_REMOTE_RUNTIME = r"C:\\EZStudioLab_assistant\\runtime"',
            SUPERVISION,
        )

    def test_deployer_stages_runtime_inside_new_clone(self):
        self.assertIn("$runtimeStaging = Join-Path $staging 'runtime'", DEPLOY)
        self.assertNotIn("$runtimeStaging = '{runtime_root}.__new'", DEPLOY)

    def test_legacy_sibling_is_cleanup_only(self):
        legacy = "C:\\\\EZStudioLab_" + "assistant_runtime"
        self.assertIn(legacy, DEPLOY)
        self.assertIn("def finalize_deployment(plan: DeployPlan)", DEPLOY)
        self.assertIn("assistant_finalize_legacy_still_present", DEPLOY)
        self.assertIn("$legacyRuntime = \'C:\\\\EZStudioLab_assistant_runtime\'", DEPLOY)

    def test_runtime_fingerprint_participates_in_up_to_date(self):
        self.assertIn("def _runtime_fingerprint()", DEPLOY)
        self.assertIn('"runtime_current": runtime_current', DEPLOY)
        self.assertIn("and runtime_current", DEPLOY)
        self.assertIn("runtime-manifest.json", DEPLOY)

    def test_supervision_state_is_inside_single_root(self):
        self.assertIn('$profileRuntime = Join-Path $root "runtime\\state"', HELPER)
        self.assertNotIn("LOCALAPPDATA", HELPER)

    def test_web_persistent_task_is_preserved(self):
        self.assertIn('$webTaskName = "EZStudioLab Assistant Web"', HELPER)
        self.assertIn("function New-WebEncodedCommand", HELPER)

    def test_running_requires_web_and_two_workers(self):
        self.assertIn(
            "if distributed_count == 1 and profile_count == 1 and web_running:",
            SUPERVISION,
        )


if __name__ == "__main__":
    unittest.main()
