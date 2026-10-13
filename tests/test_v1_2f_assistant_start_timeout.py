from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(
    encoding="utf-8-sig"
)


class V12fAssistantStartTimeoutContract(unittest.TestCase):
    def test_remote_worker_singleton_wait_allows_task_scheduler_startup(self):
        self.assertNotIn("Wait-ForSingleton", HELPER)

    def test_outer_ssh_timeout_exceeds_two_sequential_worker_waits(self):
        start = SUP.split("    def start(self) -> dict:", 1)[1].split(
            "    def stop(self) -> dict:", 1
        )[0]
        self.assertIn('timeout=75,', start)
        self.assertNotIn('timeout=30,', start)

    def test_stop_never_targets_null_or_pid_zero(self):
        self.assertIn("$matches = @()", HELPER)
        self.assertIn("$matches += @(Get-DistributedMatches)", HELPER)
        self.assertIn("$matches += @(Get-ProfileMatches)", HELPER)
        self.assertIn("if ($null -eq $proc)", HELPER)
        self.assertIn("if ($pidValue -le 0)", HELPER)
        self.assertIn("Stop-Process -Id $pidValue", HELPER)
        self.assertNotIn("@((Get-DistributedMatches) + (Get-ProfileMatches))", HELPER)


    def test_readiness_is_owned_by_python_supervisor(self):
        self.assertNotIn("Wait-ForSingleton", HELPER)
        self.assertIn("deadline = time.monotonic() + 45.0", SUP)
        self.assertIn("time.sleep(0.5)", SUP)
        self.assertIn("status = self.status(force=True)", SUP)

    def test_worker_task_powershell_wrappers_are_hidden(self):
        self.assertIn("-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand", HELPER)

    def test_worker_tasks_use_gui_subsystem_hidden_launcher(self):
        self.assertIn('$hiddenLauncherPath = Join-Path $profileRuntime "assistant-worker-hidden.vbs"', HELPER)
        self.assertIn('-Execute "wscript.exe"', HELPER)
        self.assertIn('shell.Run(cmd, 0, True)', HELPER)
        self.assertIn('Ensure-HiddenTaskLauncher', HELPER)

    def test_no_claim_or_scientific_activation(self):
        self.assertNotIn("distributed-claim-once", HELPER)
        self.assertNotIn("jobs/claim", HELPER)


if __name__ == "__main__":
    unittest.main()