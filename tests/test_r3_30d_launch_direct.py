from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")


class R330DLaunchDirectContract(unittest.TestCase):
    def test_orchestrator_is_started_directly_with_python(self):
        self.assertIn("Start-Process $Python", LAUNCHER)
        self.assertIn('"control_center.web"', LAUNCHER)
        self.assertIn('"--port", "8700", "--no-browser"', LAUNCHER)

    def test_ready_is_written_after_listener_ownership_check(self):
        check_pos = LAUNCHER.index("Test-EzsControlCenterProcess -ProcessId $newPid")
        ready_pos = LAUNCHER.index("Set-Content -LiteralPath $ReadyFile")
        self.assertLess(check_pos, ready_pos)

    def test_failure_marker_is_written_before_best_effort_error_log(self):
        failure_pos = LAUNCHER.rindex("Set-Content -LiteralPath $FailureFile")
        add_log_pos = LAUNCHER.rindex("Add-Content -Path $ErrLog")
        self.assertLess(failure_pos, add_log_pos)


if __name__ == "__main__":
    unittest.main()
