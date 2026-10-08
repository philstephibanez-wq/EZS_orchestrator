from __future__ import annotations
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class R317DTestsHotfixContract(unittest.TestCase):
    def test_header_obsolete_literal_removed(self):
        src=(ROOT/"tests"/"test_orchestrator_v1_0_4_header.py").read_text(encoding="utf-8")
        self.assertNotIn("Control Center local · 127.0.0.1:8700",src)

    def test_modal_contract_not_minification_sensitive(self):
        src=(ROOT/"tests"/"test_orchestrator_v1_0_7_3_deploy_modal.py").read_text(encoding="utf-8")
        self.assertIn("'const confirmed=await openDeploymentModal(fresh);'",src)
        self.assertIn("'if(!confirmed)return;'",src)
        self.assertNotIn("const confirmed=await openDeploymentModal(fresh);if(!confirmed)return;",src)

    def test_claim_failure_fake_executor_matches_current_api(self):
        src=(ROOT/"tests"/"test_r3_3_claim_failure_cleanup.py").read_text(encoding="utf-8")
        self.assertIn("def run(self, job, on_output=None, on_progress=None):",src)

    def test_prod_php_expectation_matches_runtime_contract(self):
        src=(ROOT/"tests"/"test_r3_12_dev_php_x64.py").read_text(encoding="utf-8")
        self.assertIn(r'H:\PHP\php-8.5-x64\php.exe',src)
        self.assertNotIn('Path("php")',src)

if __name__=="__main__":
    unittest.main()
