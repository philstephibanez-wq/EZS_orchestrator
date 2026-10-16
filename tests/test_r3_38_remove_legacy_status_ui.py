from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(
    encoding="utf-8-sig"
)

class R338RemoveLegacyStatusUiContract(unittest.TestCase):
    def test_version_stays_1_2m(self):
        self.assertEqual(
            "1.2p",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_legacy_python_status_ui_is_not_started(self):
        self.assertNotIn("status_window.pyw", HELPER)
        self.assertNotIn("$statusTaskName", HELPER)

    def test_stop_cleans_legacy_task_if_left_over(self):
        self.assertIn('"EZStudioLab Assistant Status"', HELPER)
        self.assertIn("Remove-TaskExact -TaskName $taskName", HELPER)

    def test_web_gets_required_environment(self):
        self.assertIn("EZSTUDIOLAB_ASSISTANT_TOKEN", HELPER)
        self.assertIn("GetNetworkCredential().Password", HELPER)
        self.assertIn("EZSTUDIOLAB_ASSISTANT_BASE_URL", HELPER)
        self.assertIn("EZSTUDIO_SHARED_MODEL_ROOT", HELPER)

    def test_web_uses_canonical_start_stop(self):
        self.assertIn('$webStartPath = Join-Path $root "scripts\\start.cmd"', HELPER)
        self.assertIn('$webStopPath = Join-Path $root "scripts\\stop.cmd"', HELPER)

if __name__ == "__main__":
    unittest.main()
