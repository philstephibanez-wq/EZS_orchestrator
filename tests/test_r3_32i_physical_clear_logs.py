from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from control_center.log_tools import LogTools

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")


class PhysicalClearContract(unittest.TestCase):
    def test_startup_uses_same_canonical_clear(self):
        self.assertIn("-m control_center.log_tools clear", LAUNCH)
        self.assertIn('result = self.log_tools.clear_logs()', WEB)

    def test_clear_physically_truncates_all_managed_logs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            managed = (
                root / "logs" / "control-center.log",
                root / "logs" / "assistant-deployment.log",
                root / "runtime" / "service" / "service.err.log",
            )
            excluded = (
                root / "runtime" / "jobs" / "job.log",
                root / "runtime" / "exports" / "old.log",
            )

            for path in (*managed, *excluded):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("DATA\n", encoding="utf-8")

            legacy = root / "runtime" / "logs" / "clear_state.json"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text('{"legacy":true}\n', encoding="utf-8")

            result = LogTools(root).clear_logs()

            self.assertEqual(result.failed, ())
            self.assertEqual(result.cleared, len(managed))
            for path in managed:
                self.assertEqual(path.stat().st_size, 0, str(path))
            for path in excluded:
                self.assertGreater(path.stat().st_size, 0, str(path))
            self.assertFalse(legacy.exists())

    def test_export_contract_is_physical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "logs" / "a.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("DATA\n", encoding="utf-8")

            target = LogTools(root).export_zip()
            with zipfile.ZipFile(target) as archive:
                manifest = json.loads(archive.read("manifest.json"))

            self.assertEqual(manifest["clear_mode"], "physical-truncate")

    def test_ui_is_explicitly_destructive(self):
        self.assertIn(
            "Effacer physiquement et complètement tous les fichiers de logs gérés",
            WEB,
        )
        self.assertNotIn("Masquer l'historique actuel des logs", WEB)


if __name__ == "__main__":
    unittest.main()
