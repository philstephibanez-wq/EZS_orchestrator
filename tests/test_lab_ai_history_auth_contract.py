import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class LabCanonicalHistoryContract(unittest.TestCase):
    def test_no_supervisor_credential_dependency(self):
        text=(ROOT/'control_center/web.py').read_text(encoding='utf-8')
        section=text.split('def _r2e_canonical_jobs(self)',1)[1].split('def _lab_scientific_jobs(self)',1)[0]
        self.assertNotIn('_configured_token()',section)
        self.assertIn('self.transport.registry.endpoint(Target.LAB).client().get(',section)
        self.assertIn('profile/ai-requests/recent?limit=80',section)

    def test_existing_lab_auth_not_duplicated(self):
        client=(ROOT/'transport/targets.py').read_text(encoding='utf-8')
        self.assertIn('EZSTUDIO_ANALYSIS_WORKER_TOKEN',client)
        self.assertIn('token = env.get(token_key) or override or ""',client)

if __name__=='__main__':
    unittest.main()
