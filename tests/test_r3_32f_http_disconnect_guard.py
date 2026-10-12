from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")


class Contract(unittest.TestCase):
    def test_disconnects_are_absorbed(self):
        self.assertIn(
            "ConnectionAbortedError,",
            WEB,
        )
        self.assertIn(
            "ConnectionResetError,",
            WEB,
        )

    def test_all_protected_posts_use_reload_wrapper(self):
        self.assertIn("async function protectedFetch(", WEB)
        self.assertIn(
            "if(r.status===403){window.location.reload()",
            WEB,
        )
        self.assertEqual(WEB.count("protectedFetch("), 5)
        self.assertNotIn('protectedFetch("/api/logs/export"', WEB)
        self.assertIn('window.location.assign("/api/logs/export")', WEB)


if __name__ == "__main__":
    unittest.main()
