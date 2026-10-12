from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")


class LogsContract(unittest.TestCase):
    def test_export_is_read_only_get(self):
        self.assertIn('window.location.assign("/api/logs/export")', WEB)
        self.assertNotIn('protectedFetch("/api/logs/export"', WEB)
        self.assertEqual(WEB.count('if path == "/api/logs/export":'), 2)
        self.assertIn("def _send_log_export(self) -> None:", WEB)

    def test_legacy_post_export_is_before_token_guard(self):
        post = WEB.index("        def do_POST(self) -> None:")
        export = WEB.index(
            '            if path == "/api/logs/export":',
            post,
        )
        guard = WEB.index(
            '            if self.headers.get("X-EZS-Token") != token:',
            post,
        )
        self.assertLess(export, guard)

    def test_clear_logs_remains_protected(self):
        self.assertIn('action("logs-clear")', WEB)
        self.assertIn('if name == "logs-clear":', WEB)
        self.assertIn(
            'if self.headers.get("X-EZS-Token") != token:',
            WEB,
        )

    def test_ui_token_survives_control_center_restart(self):
        self.assertIn(
            "def _load_or_create_ui_token(runtime: Path) -> str:",
            WEB,
        )
        self.assertIn(
            'runtime / "control-center-ui.token"',
            WEB,
        )
        self.assertIn(
            "token = _load_or_create_ui_token(",
            WEB,
        )
        self.assertNotIn(
            "token = secrets.token_urlsafe(24)",
            WEB,
        )


if __name__ == "__main__":
    unittest.main()
