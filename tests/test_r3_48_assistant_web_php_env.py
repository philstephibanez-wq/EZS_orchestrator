from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "assistant_supervision" / "remote_helper.ps1"

class R348AssistantWebPhpEnvContract(unittest.TestCase):
    def test_web_task_reloads_persistent_php_override(self):
        text = HELPER.read_text(encoding="utf-8-sig")
        self.assertIn("GetEnvironmentVariable('EZS_ASSISTANT_PHP','User')", text)
        self.assertIn("GetEnvironmentVariable('EZS_ASSISTANT_PHP','Machine')", text)
        self.assertIn("`$env:EZS_ASSISTANT_PHP = `$phpOverride", text)

    def test_php_override_is_set_before_web_start(self):
        text = HELPER.read_text(encoding="utf-8-sig")
        env_pos = text.index("`$env:EZS_ASSISTANT_PHP = `$phpOverride")
        start_pos = text.index("& '$webStartPath'", env_pos)
        self.assertLess(env_pos, start_pos)

if __name__ == "__main__":
    unittest.main()
