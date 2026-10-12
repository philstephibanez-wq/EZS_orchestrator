from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAT_BYTES = (ROOT / "launch.bat").read_bytes()
LAUNCHER = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")
LOG_TOOLS = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")


class R330FLaunchPurgeFixContract(unittest.TestCase):
    def test_batch_has_no_utf8_bom(self):
        self.assertFalse(BAT_BYTES.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(BAT_BYTES.startswith(b"@echo off"))

    def test_launcher_uses_module_cli_not_python_dash_c(self):
        self.assertIn("& $Python -m control_center.log_tools clear", LAUNCHER)
        self.assertNotIn("$logPurgeCode", LAUNCHER)
        self.assertNotIn("& $Python -c", LAUNCHER)

    def test_log_tools_exposes_clear_cli(self):
        self.assertIn('if len(sys.argv) != 2 or sys.argv[1] != "clear":', LOG_TOOLS)
        self.assertIn("result = LogTools(load_runtime_config().orchestrator_root).clear_logs()", LOG_TOOLS)
        self.assertIn('print(f"LOGS_PURGED cleared={result.cleared} failed={len(result.failed)}")', LOG_TOOLS)


if __name__ == "__main__":
    unittest.main()
