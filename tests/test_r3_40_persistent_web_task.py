from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(
    encoding="utf-8-sig"
)
MANAGER = (ROOT / "assistant_supervision" / "manager.py").read_text(
    encoding="utf-8"
)

class R340PersistentWebTaskContract(unittest.TestCase):
    def test_version_stays_1_2m(self):
        self.assertEqual(
            "1.2p",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_web_is_persistent_scheduled_task(self):
        self.assertIn('$webTaskName = "EZStudioLab Assistant Web"', HELPER)
        self.assertIn("function New-WebEncodedCommand", HELPER)
        self.assertIn("-TaskName $webTaskName", HELPER)
        self.assertIn("assistant_web_listener_lost", HELPER)

    def test_web_not_started_directly_from_ssh(self):
        self.assertNotIn(
            '& $webStartPath\nif ($LASTEXITCODE -ne 0)',
            HELPER,
        )

    def test_stop_removes_web_task(self):
        self.assertIn(
            '@($distributedTaskName,$profileTaskName,$webTaskName,"EZStudioLab Assistant Status")',
            HELPER,
        )

    def test_manager_running_requires_web(self):
        self.assertIn(
            "distributed_count == 1 and profile_count == 1 and web_running",
            MANAGER,
        )
        self.assertIn("assistant_web_start_not_running", MANAGER)

    def test_manager_compiles(self):
        py_compile.compile(
            str(ROOT / "assistant_supervision" / "manager.py"),
            doraise=True,
        )

if __name__ == "__main__":
    unittest.main()
