from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAT = (ROOT / "launch.bat").read_text(encoding="utf-8-sig")
HIDDEN = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")
SPLASH = (ROOT / "scripts" / "show_splash.ps1").read_text(encoding="utf-8-sig")


class R325LauncherSplashContract(unittest.TestCase):
    def test_launch_bat_is_detached(self):
        self.assertNotIn('start "" /b powershell.exe', BAT.lower())
        self.assertIn('start "" powershell.exe', BAT.lower())
        self.assertIn("launch_hidden.ps1", BAT)
        self.assertIn("exit /b 0", BAT)

    def test_splash_is_started_immediately(self):
        self.assertIn("show_splash.ps1", HIDDEN)
        self.assertIn("Start-Process powershell.exe", HIDDEN)
        self.assertIn("-WindowStyle Hidden", HIDDEN)
        self.assertIn('"-STA"', HIDDEN)
        self.assertIn("ReadyFile", HIDDEN)
        self.assertIn("FailureFile", HIDDEN)

    def test_splash_waits_for_verified_control_center(self):
        ready_write = HIDDEN.index("Set-Content -LiteralPath $ReadyFile")
        listener_check = HIDDEN.index("Test-EzsControlCenterProcess -ProcessId $newPid")
        browser_open = HIDDEN.index("Start-Process $ControlCenterUrl")
        self.assertGreater(ready_write, listener_check)
        self.assertGreater(browser_open, ready_write)

    def test_existing_port_safety_is_preserved(self):
        self.assertIn("Stop-ExistingControlCenter", HIDDEN)
        self.assertIn("processus étranger", HIDDEN)
        self.assertIn("Stop-Process -Id $pid8700 -Force", HIDDEN)

    def test_service_all_target_is_preserved(self):
        self.assertIn("service.service_cli start --target all", HIDDEN)

    def test_splash_is_borderless_and_self_closing(self):
        self.assertIn("FormBorderStyle]::None", SPLASH)
        self.assertIn("ShowInTaskbar = $false", SPLASH)
        self.assertIn("Test-Path -LiteralPath $ReadyFile", SPLASH)
        self.assertIn("$form.Close()", SPLASH)

    def test_progress_is_deterministic_and_visible(self):
        self.assertIn("ProgressBarStyle]::Continuous", SPLASH)
        self.assertIn("$progressValue = 4", SPLASH)
        self.assertIn("$progressValue -lt 92", SPLASH)
        self.assertIn("$progress.Value = $progressValue", SPLASH)
        self.assertIn("$progress.Value = 100", SPLASH)
        self.assertNotIn("ProgressBarStyle]::Marquee", SPLASH)


if __name__ == "__main__":
    unittest.main()
