from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
SUP = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8")
HELPER = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")


class R337GitDeployRemoteStartContract(unittest.TestCase):
    def test_version_stays_1_2m(self):
        self.assertEqual("1.2n", (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip())

    def test_status_uses_remote_git_head(self):
        self.assertIn("git -C $root rev-parse HEAD", DEPLOY)
        self.assertNotIn("DEPLOYED_COMMIT.txt", DEPLOY)

    def test_deploy_uses_clean_clone(self):
        self.assertIn("git clone --branch main --single-branch", DEPLOY)
        self.assertIn("remote_worktree_not_clean", DEPLOY)
        self.assertIn("COMPOSER_LOCK_IDENTICAL reuse_vendor", DEPLOY)

    def test_runtime_is_external(self):
        self.assertIn(r'C:\EZStudioLab_assistant\runtime', DEPLOY)
        self.assertIn(r'C:\EZStudioLab_assistant\runtime', SUP)
        self.assertIn('self.remote_runtime + r"\\assistant-supervision.ps1"', SUP)

    def test_remote_helper_drives_canonical_web_commands(self):
        self.assertIn('$root = "C:\\EZStudioLab_assistant"', HELPER)
        self.assertIn('$webStartPath = Join-Path $root "scripts\\start.cmd"', HELPER)
        self.assertIn('$webStopPath = Join-Path $root "scripts\\stop.cmd"', HELPER)

    def test_modified_python_compiles(self):
        py_compile.compile(str(ROOT / "assistant_deployment" / "manager.py"), doraise=True)
        py_compile.compile(str(ROOT / "assistant_supervision" / "manager.py"), doraise=True)


if __name__ == "__main__":
    unittest.main()
