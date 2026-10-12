from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCH_BAT = (ROOT / "launch.bat").read_text(encoding="utf-8-sig")


class R330ALaunchDetachContract(unittest.TestCase):
    def test_launcher_does_not_attach_child_to_calling_console(self):
        self.assertNotIn("start \"\" /b powershell.exe", LAUNCH_BAT.lower())
        self.assertIn("start \"\" powershell.exe", LAUNCH_BAT.lower())

    def test_hidden_launcher_is_preserved(self):
        self.assertIn("-WindowStyle Hidden", LAUNCH_BAT)
        self.assertIn("-File \"%~dp0scripts\\launch_hidden.ps1\"", LAUNCH_BAT)


if __name__ == "__main__":
    unittest.main()
