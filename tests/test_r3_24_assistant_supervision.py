from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")

class R324AssistantSupervisionContract(unittest.TestCase):
    def test_controlled_runtime(self):
        self.assertIn("def start(self) -> dict:", SUP)
        self.assertIn("def stop(self) -> dict:", SUP)
        self.assertIn("Start-Process", SUP)
        self.assertIn("Stop-Process -Id", SUP)
        self.assertNotIn("Stop-Process -Name", SUP)

    def test_watch_only(self):
        self.assertIn("'distributed-watch'", SUP)
        self.assertNotIn("distributed-claim-once", SUP)
        self.assertNotIn("jobs/claim", SUP)

    def test_secret_not_command_line(self):
        self.assertIn("[Console]::In.ReadLine()", SUP)
        self.assertIn("stdin_text=token +", SUP)
        self.assertNotIn("'--token'", SUP)

    def test_interactive_tray_window(self):
        self.assertIn("status_window.pyw", SUP)
        self.assertIn("pythonw.exe", SUP)
        self.assertIn("Unregister-ScheduledTask", SUP)
        self.assertNotIn("status_window.ps1", SUP)
        self.assertIn("Interactive", SUP)
        self.assertIn("Start-ScheduledTask", SUP)

    def test_operator_buttons(self):
        self.assertIn('id="assistantStart"', WEB)
        self.assertIn('id="assistantStop"', WEB)
        self.assertIn('"/api/assistant/supervision/start"', WEB)
        self.assertIn('"/api/assistant/supervision/stop"', WEB)

if __name__ == "__main__":
    unittest.main()
