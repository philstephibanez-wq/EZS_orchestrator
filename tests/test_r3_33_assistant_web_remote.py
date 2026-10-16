from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")
MANAGER = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")


class R333AssistantWebRemoteContract(unittest.TestCase):
    def test_release_version(self):
        self.assertEqual("1.2o", (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_remote_start_uses_canonical_web_singleton(self):
        self.assertIn('$webStartPath = Join-Path $root "scripts\\start.cmd"', HELPER)
        self.assertIn("function New-WebEncodedCommand", HELPER)
        self.assertIn("-TaskName $webTaskName", HELPER)
        self.assertIn("assistant_web_start_listener_missing", HELPER)

    def test_remote_start_exports_web_dependencies(self):
        self.assertIn("EZSTUDIOLAB_ASSISTANT_TOKEN", HELPER)
        self.assertIn("GetNetworkCredential().Password", HELPER)
        self.assertIn("EZSTUDIOLAB_ASSISTANT_BASE_URL", HELPER)
        self.assertIn("EZSTUDIO_SHARED_MODEL_ROOT", HELPER)

    def test_remote_stop_uses_canonical_stop_and_verifies_ports(self):
        self.assertIn('$webStopPath = Join-Path $root "scripts\\stop.cmd"', HELPER)
        self.assertIn("& $webStopPath", HELPER)
        self.assertIn("assistant_web_stop_incomplete", HELPER)
        self.assertIn("8712,8713", HELPER)

    def test_supervision_status_includes_web(self):
        self.assertIn("web_running: bool", MANAGER)
        self.assertIn("web_listener_count: int", MANAGER)
        self.assertIn("web_version: str | None", MANAGER)
        self.assertIn('"web_running": self.web_running', MANAGER)
        self.assertIn("Get-NetTCPConnection -State Listen -LocalPort 8712,8713", MANAGER)

    def test_start_requires_web_and_workers(self):
        self.assertIn("assistant_web_start_not_running", MANAGER)
        self.assertIn("assistant_web_start_not_singleton", MANAGER)
        self.assertIn("assistant_distributed_start_not_singleton", MANAGER)
        self.assertIn("assistant_profile_start_not_singleton", MANAGER)

    def test_stop_requires_web_stopped(self):
        self.assertIn("assistant_web_stop_still_running", MANAGER)


if __name__ == "__main__":
    unittest.main()
