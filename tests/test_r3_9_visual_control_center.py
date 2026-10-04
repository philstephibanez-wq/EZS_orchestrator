from __future__ import annotations
import unittest
from pathlib import Path
from control_center import web

class R39VisualControlCenterContractTest(unittest.TestCase):
    def test_loopback_only(self):
        self.assertEqual(web.HOST, "127.0.0.1")
        self.assertEqual(web.DEFAULT_PORT, 8700)

    def test_prod_mutations_are_limited_to_protected_lifecycle(self):
        source = Path(web.__file__).read_text(encoding="utf-8")
        # R3.10 deliberately authorizes only protected PROD operations from the
        # local Control Center; arbitrary deployment/business mutations remain absent.
        for term in (
            "prod-lifecycle-start",
            "prod-lifecycle-stop",
            "prod-lifecycle-restart",
            "prod-mode-normal",
            "prod-mode-maintenance",
        ):
            self.assertIn(term, source)
        for forbidden in (
            "prod-deploy",
            "prod-db-",
            "prod-analysis-",
            "prod-storage-",
            "service-start-prod",
        ):
            self.assertNotIn(forbidden, source)

    def test_token_required(self):
        source = Path(web.__file__).read_text(encoding="utf-8")
        self.assertIn("X-EZS-Token", source)
        self.assertIn("secrets.token_urlsafe", source)

    def test_existing_managers_reused(self):
        source = Path(web.__file__).read_text(encoding="utf-8")
        for term in ("ServerManager","CaddyManager","JobTransport","analysis_execution_active"):
            self.assertIn(term, source)

if __name__ == "__main__":
    unittest.main()
