from __future__ import annotations
import unittest
from pathlib import Path
from control_center import web

class R39VisualControlCenterContractTest(unittest.TestCase):
    def test_loopback_only(self):
        self.assertEqual(web.HOST, "127.0.0.1")
        self.assertEqual(web.DEFAULT_PORT, 8700)

    def test_prod_has_no_mutating_visual_action(self):
        source = Path(web.__file__).read_text(encoding="utf-8")
        for term in ("prod-server-start","prod-server-stop","prod-server-restart","prod-caddy-start","service-start-prod"):
            self.assertNotIn(term, source)

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
