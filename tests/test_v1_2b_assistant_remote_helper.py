from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")


class V12bAssistantRemoteHelperContract(unittest.TestCase):
    def test_start_uses_short_remote_helper_command(self):
        self.assertIn("def _run_remote_helper(", SUP)
        start = SUP.split("    def start(self) -> dict:", 1)[1].split(
            "    def stop(self) -> dict:", 1
        )[0]
        self.assertIn('self._run_remote_helper(', start)
        self.assertIn('"start"', start)
        self.assertNotIn("Start-Process", start)
        self.assertNotIn("-EncodedCommand", start)

    def test_helper_is_bundled_and_verified(self):
        self.assertIn("SUPERVISION_HELPER", DEPLOY)
        self.assertIn("assistant-supervision.ps1", DEPLOY)
        self.assertIn("assistant_runtime_helper_missing", DEPLOY)
        self.assertIn("remote_supervision_helper_missing_after_install", DEPLOY)

    def test_token_transport_remains_stdin_only(self):
        self.assertIn("[Console]::In.ReadLine()", HELPER)
        self.assertIn("stdin_text=token +", SUP)
        self.assertNotIn('"--token"', HELPER)
        self.assertNotIn("'--token'", SUP)

    def test_helper_has_both_exact_watch_processes(self):
        self.assertIn('"distributed-watch"', HELPER)
        self.assertIn('"profile-review-auto-watch"', HELPER)
        self.assertIn("Stop-Process -Id", HELPER)
        self.assertNotIn("Stop-Process -Name", HELPER)


if __name__ == "__main__":
    unittest.main()
