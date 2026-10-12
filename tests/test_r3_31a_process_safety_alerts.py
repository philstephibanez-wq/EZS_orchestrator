from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
LOG_TOOLS = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")


class R331AProcessSafetyAlertsContract(unittest.TestCase):
    def test_snapshot_contains_safety_status(self):
        self.assertIn('data["safety"] = self._safety_status(data)', WEB)
        self.assertIn("heartbeat_stale", WEB)
        self.assertIn("foreign_process", WEB)
        self.assertIn("http_unreachable", WEB)
        self.assertIn("queue_error", WEB)

    def test_persistent_visible_notification_exists(self):
        self.assertIn('id="safetyBanner"', WEB)
        self.assertIn('id="safetyTitle"', WEB)
        self.assertIn('id="safetyDetail"', WEB)
        self.assertIn('id="safetyLogs"', WEB)
        self.assertIn("function renderSafety", WEB)
        self.assertIn("ERREUR DÉTECTÉE", WEB)

    def test_log_error_detection_uses_visible_post_purge_lines(self):
        self.assertIn("def error_alerts(", LOG_TOOLS)
        self.assertIn("self.tail(path", LOG_TOOLS)
        lowered = LOG_TOOLS.lower()
        self.assertIn("connectionabortederror", lowered)
        self.assertIn("winerror 10053", lowered)
        self.assertIn("context canceled", lowered)

    def test_monitor_is_read_only(self):
        start = WEB.index("    def _safety_status")
        end = WEB.index("    def _snapshot_uncached", start)
        section = WEB[start:end]
        self.assertNotIn("Stop-Process", section)
        self.assertNotIn("terminate(", section)
        self.assertNotIn("kill(", section)


if __name__ == "__main__":
    unittest.main()
