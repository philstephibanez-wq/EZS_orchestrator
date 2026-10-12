from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
SUPERVISOR = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")


class R324AssistantSupervisionContract(unittest.TestCase):
    def test_read_only_supervisor_exists(self):
        self.assertIn("class AssistantSupervisor", SUPERVISOR)
        self.assertIn("def status(self, force: bool = False)", SUPERVISOR)
        self.assertIn("def tail(self, stream: str, lines: int = 250)", SUPERVISOR)
        self.assertIn("Get-CimInstance Win32_Process", SUPERVISOR)
        self.assertNotIn("Start-Process", SUPERVISOR)
        self.assertNotIn("Stop-Process", SUPERVISOR)

    def test_remote_logs_are_dedicated(self):
        self.assertIn("assistant.out.log", SUPERVISOR)
        self.assertIn("assistant.err.log", SUPERVISOR)
        self.assertIn('self.log_root = remote_root + r"\\logs"', SUPERVISOR)
        self.assertIn('data-log="assistant_xps"', WEB)
        self.assertIn('data-log="assistant_xps_error"', WEB)

    def test_control_center_has_supervision_routes(self):
        self.assertIn('"/api/assistant/supervision/status"', WEB)
        self.assertIn('"/api/assistant/logs"', WEB)
        self.assertIn("assistant_supervision_status(self)", WEB)
        self.assertIn("assistant_logs(self, stream: str)", WEB)

    def test_runtime_state_visible_in_assistant_card(self):
        self.assertIn('id="assistantRuntimeState"', WEB)
        self.assertIn("function renderAssistantSupervision(payload)", WEB)
        for state in ("STOPPED", "ONLINE", "BUSY", "STALE", "ERROR"):
            self.assertIn(f'"{state}"', WEB)

    def test_remote_supervision_has_slower_poll(self):
        self.assertNotIn("setInterval(refreshAssistantSupervision,3000)", WEB)
        self.assertIn("setInterval(refreshAssistantSupervision,10000)", WEB)

    def test_scientific_execution_is_not_started(self):
        self.assertNotIn("distributed-probe", SUPERVISOR)
        self.assertNotIn("distributed-watch", SUPERVISOR)
        self.assertNotIn("jobs/claim", SUPERVISOR)


if __name__ == "__main__":
    unittest.main()
