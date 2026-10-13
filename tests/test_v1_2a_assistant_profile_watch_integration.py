from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")


class V12aAssistantProfileWatchIntegration(unittest.TestCase):
    def test_existing_runtime_deployment_model_is_preserved(self):
        self.assertIn(r'C:\EZStudioLab_assistant', DEPLOY)
        self.assertIn(r'C:\EZStudioLab_assistant\runtime', DEPLOY)
        self.assertIn('["git", "archive", "--format=zip"', DEPLOY)
        self.assertNotIn("git clone", DEPLOY)
        self.assertNotIn("git pull", DEPLOY)

    def test_deployment_transport_is_bounded(self):
        self.assertGreaterEqual(DEPLOY.count("timeout=120"), 2)
        self.assertIn("assistant_scp_timeout", DEPLOY)
        self.assertIn("assistant_remote_install_timeout", DEPLOY)
        self.assertIn("except subprocess.TimeoutExpired as exc:", DEPLOY)

    def test_profile_watch_is_started_by_existing_supervisor(self):
        self.assertIn('"profile-review-auto-watch"', HELPER)
        self.assertIn('"--poll-seconds","900"', HELPER)
        self.assertIn('"--draft-cooldown-hours","24"', HELPER)
        self.assertIn('"--abstain-cooldown-hours","168"', HELPER)
        self.assertIn('"--max-items","5"', HELPER)
        self.assertIn('"--network-max-requests","6"', HELPER)
        self.assertIn("profile-review-watch.state.json", HELPER)

    def test_profile_state_survives_runtime_redeploy(self):
        self.assertIn("$env:LOCALAPPDATA", HELPER)
        self.assertIn("EZStudioLab_assistant\\runtime", HELPER)

    def test_supervision_is_exact_and_secret_stays_off_command_line(self):
        self.assertIn("assistant_duplicate_distributed_processes", HELPER)
        self.assertIn("assistant_duplicate_profile_processes", HELPER)
        self.assertIn("profile_review_count", SUP)
        self.assertIn("Stop-Process -Id", HELPER)
        self.assertNotIn("Stop-Process -Name", HELPER)
        self.assertIn("[Console]::In.ReadLine()", HELPER)
        self.assertIn("stdin_text=token +", SUP)
        self.assertNotIn("'--token'", SUP)
        self.assertNotIn('"--token"', HELPER)

    def test_distributed_scientific_execution_contract_unchanged(self):
        self.assertIn('"distributed-watch"', HELPER)
        self.assertNotIn("distributed-claim-once", SUP + HELPER)
        self.assertNotIn("jobs/claim", SUP + HELPER)


if __name__ == "__main__":
    unittest.main()
