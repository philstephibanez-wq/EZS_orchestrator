from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(
    encoding="utf-8-sig"
)


class V12eAssistantPersistentSupervisionContract(unittest.TestCase):
    def test_workers_are_task_scheduler_owned(self):
        self.assertIn("EZStudioLab Assistant Distributed", HELPER)
        self.assertIn("EZStudioLab Assistant Profile", HELPER)
        self.assertIn("Register-PersistentTask", HELPER)
        self.assertIn("New-ScheduledTaskSettingsSet", HELPER)
        self.assertIn("ExecutionTimeLimit ([TimeSpan]::Zero)", HELPER)
        self.assertIn("Wait-ForSingleton -Mode distributed", HELPER)
        self.assertIn("Wait-ForSingleton -Mode profile", HELPER)

    def test_workers_keep_current_modes(self):
        self.assertIn('"distributed-watch"', HELPER)
        self.assertIn('"profile-review-auto-watch"', HELPER)
        self.assertNotIn("distributed-claim-once", HELPER)

    def test_secret_is_dpapi_protected_and_not_cli(self):
        self.assertIn("analysis-worker-token.dpapi", HELPER)
        self.assertIn("ConvertFrom-SecureString", HELPER)
        self.assertIn("ConvertTo-SecureString", HELPER)
        self.assertIn("[Console]::In.ReadLine()", HELPER)
        self.assertNotIn("'--token'", HELPER)
        self.assertNotIn('"--token"', HELPER)

    def test_stop_is_exact_and_removes_tasks(self):
        self.assertIn("Remove-TaskExact -TaskName", HELPER)
        self.assertIn("Stop-Process -Id", HELPER)
        self.assertNotIn("Stop-Process -Name", HELPER)

    def test_no_scientific_activation(self):
        self.assertNotIn("distributed-claim-once", HELPER)
        self.assertNotIn("jobs/claim", HELPER)


if __name__ == "__main__":
    unittest.main()