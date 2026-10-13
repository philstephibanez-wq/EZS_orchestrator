from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")

class R324AssistantSupervisionContract(unittest.TestCase):
    def test_controlled_runtime(self):
        self.assertIn("def start(self) -> dict:", SUP)
        self.assertIn("def stop(self) -> dict:", SUP)
        self.assertIn("Register-ScheduledTask", HELPER)
        self.assertIn("Start-ScheduledTask", HELPER)
        self.assertIn("Stop-ScheduledTask", HELPER)
        self.assertIn("Stop-Process -Id", HELPER)
        self.assertNotIn("Stop-Process -Name", HELPER)

    def test_watch_only(self):
        self.assertIn('"distributed-watch"', HELPER)
        self.assertNotIn("distributed-claim-once", SUP + HELPER)
        self.assertNotIn("jobs/claim", SUP + HELPER)

    def test_secret_not_command_line(self):
        self.assertIn("[Console]::In.ReadLine()", HELPER)
        self.assertIn("stdin_text=token +", SUP)
        self.assertIn("ConvertFrom-SecureString", HELPER)
        self.assertIn("ConvertTo-SecureString", HELPER)
        self.assertIn("analysis-worker-token.dpapi", HELPER)
        self.assertNotIn("'--token'", SUP)
        self.assertNotIn('"--token"', HELPER)

    def test_interactive_tray_window(self):
        self.assertIn("status_window.pyw", HELPER)
        self.assertIn("pythonw.exe", HELPER)
        self.assertIn("Unregister-ScheduledTask", HELPER)
        self.assertNotIn("status_window.ps1", HELPER)
        self.assertIn("Interactive", HELPER)
        self.assertIn("Start-ScheduledTask", HELPER)

    def test_operator_buttons(self):
        self.assertIn('id="assistantStart"', WEB)
        self.assertIn('id="assistantStop"', WEB)
        self.assertIn('"/api/assistant/supervision/start"', WEB)
        self.assertIn('"/api/assistant/supervision/stop"', WEB)

if __name__ == "__main__":
    unittest.main()
