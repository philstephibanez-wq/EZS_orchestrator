from __future__ import annotations
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=(ROOT/"service"/"service_cli.py").read_text(encoding="utf-8")
PS=(ROOT/"scripts"/"launch_hidden.ps1").read_text(encoding="utf-8-sig")
class Contract(unittest.TestCase):
    def test_reload_is_idle_safe(self):
        self.assertIn("def restart_if_idle(",CLI)
        self.assertIn("analysis_execution_active",CLI)
        self.assertIn("SERVICE_RELOAD_SKIPPED active_analysis",CLI)
        self.assertIn("restart-if-idle",PS)
        self.assertNotIn("Stop-Process -Name",PS)
    def test_service_identity_is_strong(self):
        self.assertIn("def _expected_service_process(",CLI)
        self.assertIn("executable_path(pid)",CLI)
        self.assertIn("command_line(pid)",CLI)
if __name__=="__main__": unittest.main()
