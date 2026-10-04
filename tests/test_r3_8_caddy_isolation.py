from __future__ import annotations

import unittest

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target


class R38CaddyIsolationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = CaddyManager(load_runtime_config())

    def test_dev_is_strictly_dev(self):
        text = self.manager._render(Target.DEV)
        # R3.10: wildcard host on the target port, but loopback-only bind.
        self.assertIn(":8502 {", text)
        self.assertIn("bind 127.0.0.1", text)
        self.assertIn("127.0.0.1:8602", text)
        self.assertIn("H:/EZScore_dev/var/storage/stems", text)
        self.assertNotIn(":8501 {", text)
        self.assertNotIn("127.0.0.1:8510", text)
        self.assertNotIn('H:/EZScore/var/storage/stems"', text)

    def test_prod_is_strictly_prod(self):
        text = self.manager._render(Target.PROD)
        # Public Host (Cloudflare) must match while Caddy remains bound to loopback.
        self.assertIn(":8501 {", text)
        self.assertIn("bind 127.0.0.1", text)
        self.assertIn("127.0.0.1:8510", text)
        self.assertIn("H:/EZScore/var/storage/stems", text)
        self.assertNotIn(":8502 {", text)
        self.assertNotIn("127.0.0.1:8602", text)
        self.assertNotIn("H:/EZScore_dev/var/storage/stems", text)

    def test_no_shared_media_root_variable(self):
        self.assertNotIn("EZSCORE_MEDIA_ROOT", self.manager._render(Target.DEV))
        self.assertNotIn("EZSCORE_MEDIA_ROOT", self.manager._render(Target.PROD))


if __name__ == "__main__":
    unittest.main()
