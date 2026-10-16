from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(
    encoding="utf-8-sig"
)

class R339LegacyPythonUiRemoved(unittest.TestCase):
    def test_orchestrator_version_stays_1_2m(self):
        self.assertEqual(
            "1.2o",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_helper_has_no_legacy_python_ui(self):
        self.assertNotIn("status_window.pyw", HELPER)
        self.assertNotIn("pythonw.exe", HELPER)
        self.assertNotIn("$statusTaskName", HELPER)

    def test_backward_cleanup_of_old_task_remains(self):
        self.assertIn('"EZStudioLab Assistant Status"', HELPER)
        self.assertIn("Remove-TaskExact -TaskName $taskName", HELPER)

if __name__ == "__main__":
    unittest.main()
