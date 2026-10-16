from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AssistantRuntimeTruthContract(unittest.TestCase):
    def test_supervision_exact_web_identity_and_foreign(self):
        text = (ROOT / "assistant_supervision" / "manager.py").read_text(encoding="utf-8-sig")
        self.assertIn("Test-AssistantPortOwner", text)
        self.assertIn("'caddy.exe'", text)
        self.assertIn("'php.exe'", text)
        self.assertIn('state = "FOREIGN"', text)
        self.assertIn("web_listener_count == 2", text)
        self.assertIn("web_listener_count == 0", text)

    def test_control_center_preserves_runtime_truth(self):
        text = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8-sig")
        self.assertIn('elif remote_state == "FOREIGN":', text)
        self.assertIn('state = "FOREIGN"', text)
        self.assertIn('FOREIGN:"PORT ÉTRANGER"', text)
        self.assertIn('const blocked=state==="FOREIGN";', text)

if __name__ == "__main__":
    unittest.main()
