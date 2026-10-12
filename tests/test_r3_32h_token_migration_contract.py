from __future__ import annotations
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = (ROOT/"scripts"/"launch_hidden.ps1").read_text(encoding="utf-8-sig")

class TokenMigrationContract(unittest.TestCase):
    def test_migration_precedes_stop_call(self):
        calls = list(re.finditer(
            r"(?m)^\s*(Preserve-CurrentControlCenterToken|Stop-ExistingControlCenter)\s*$",
            LAUNCH,
        ))
        names = [m.group(1) for m in calls[-2:]]
        self.assertEqual(
            names,
            ["Preserve-CurrentControlCenterToken", "Stop-ExistingControlCenter"],
        )

    def test_token_not_printed(self):
        self.assertIn('Join-Path $Runtime "control-center-ui.token"', LAUNCH)
        self.assertIn('[A-Za-z0-9_-]{32,}', LAUNCH)
        self.assertNotIn("Write-Host $token", LAUNCH)
        self.assertNotIn("Write-Output $token", LAUNCH)

    def test_fail_closed_before_stop(self):
        block = LAUNCH[
            LAUNCH.index("function Preserve-CurrentControlCenterToken"):
            LAUNCH.index("function Stop-ExistingControlCenter")
        ]
        self.assertIn("Invoke-WebRequest", block)
        self.assertIn("-TimeoutSec 3", block)
        self.assertGreaterEqual(block.count("Aucun arrêt effectué."), 3)

    def test_existing_token_is_preserved(self):
        block = LAUNCH[
            LAUNCH.index("function Preserve-CurrentControlCenterToken"):
            LAUNCH.index("function Stop-ExistingControlCenter")
        ]
        self.assertIn("Test-Path -LiteralPath $tokenPath -PathType Leaf", block)
        self.assertIn("return", block)

if __name__ == "__main__":
    unittest.main()
