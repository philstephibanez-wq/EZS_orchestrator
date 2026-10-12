from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")
LOG_TOOLS = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")

class R330BLaunchStartupContract(unittest.TestCase):
    def test_splash_host_is_hidden(self):
        marker = 'if (Test-Path -LiteralPath $SplashScript -PathType Leaf) {'
        start = LAUNCHER.index(marker)
        block = LAUNCHER[start: start + 500]
        self.assertIn("Start-Process powershell.exe", block)
        self.assertIn("-WindowStyle Hidden", block)

    def test_runtime_log_scan_prunes_heavy_directories_before_recursing(self):
        self.assertIn('excluded_runtime_dirs = {"jobs", "exports"}', LOG_TOOLS)
        self.assertIn("for child in runtime.iterdir()", LOG_TOOLS)
        self.assertIn("if child.name.lower() in excluded_runtime_dirs:", LOG_TOOLS)
        self.assertNotIn('for base in (self.root / "logs", self.root / "runtime"):', LOG_TOOLS)

if __name__ == "__main__":
    unittest.main()
