from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")
LOG_TOOLS = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")


class R330LogPurgeOnRestartContract(unittest.TestCase):
    def test_launcher_purges_visible_logs_before_restart(self):
        self.assertIn("& $Python -m control_center.log_tools clear", LAUNCHER)
        self.assertIn("Impossible de purger les logs au redémarrage.", LAUNCHER)
        purge_pos = LAUNCHER.index("& $Python -m control_center.log_tools clear")
        service_pos = LAUNCHER.index("# 1. Ensure the permanent service is running.")
        self.assertLess(purge_pos, service_pos)

    def test_purge_is_logical_and_keeps_protected_audit(self):
        self.assertIn('PROTECTED_AUDIT_LOGS = {"logs/assistant-deployment.log"}', LOG_TOOLS)
        self.assertIn("if self._relative_key(path) in self.PROTECTED_AUDIT_LOGS:", LOG_TOOLS)
        self.assertIn("offset", LOG_TOOLS)

    def test_launcher_reports_purge_result_via_module_cli(self):
        self.assertIn("$logPurgeOutput", LAUNCHER)
        self.assertIn("$logPurgeExitCode", LAUNCHER)
        self.assertIn('print(f"LOGS_PURGED cleared={result.cleared} failed={len(result.failed)}")', LOG_TOOLS)


if __name__ == "__main__":
    unittest.main()
