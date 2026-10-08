from __future__ import annotations

import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class R317CTestsHotfixContract(unittest.TestCase):
    def test_hotfix_changes_tests_only(self):
        migration=(ROOT/"scripts"/"migrate-lab-r3_17c-tests-hotfix.py").read_text(encoding="utf-8")
        for forbidden in (
            'ROOT/"control_center"/"web.py"',
            'ROOT/"config"/"runtime.json"',
            'ROOT/"executor"/"planner.py"',
            'ROOT/"service"/"runner.py"',
            'ROOT/"transport"/"targets.py"',
        ):
            self.assertNotIn(forbidden,migration)

    def test_claim_failure_double_supports_progress_callback(self):
        src=(ROOT/"tests"/"test_r3_3_claim_failure_cleanup.py").read_text(encoding="utf-8")
        self.assertIn("def run(self, job, on_output=None, on_progress=None):",src)

    def test_prod_php_expectation_matches_current_v1_contract(self):
        src=(ROOT/"tests"/"test_r3_12_dev_php_x64.py").read_text(encoding="utf-8")
        self.assertIn(r'H:\PHP\php-8.5-x64\php.exe',src)
        self.assertNotIn('Path("php")',src)

    def test_deploy_modal_contract_is_not_whitespace_sensitive(self):
        src=(ROOT/"tests"/"test_orchestrator_v1_0_7_3_deploy_modal.py").read_text(encoding="utf-8")
        self.assertIn("'const confirmed=await openDeploymentModal(fresh);'",src)
        self.assertIn("'if(!confirmed)return;'",src)

if __name__=="__main__":
    unittest.main()
