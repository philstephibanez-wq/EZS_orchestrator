from __future__ import annotations

import unittest

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target


class DevCoverStaticContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = CaddyManager(load_runtime_config())

    def test_dev_cover_route(self):
        rendered = self.manager._render(Target.DEV)
        self.assertIn("@covers path /uploads/covers/*", rendered)
        self.assertIn('root * "H:/EZScore_dev/var/storage/covers"', rendered)
        self.assertIn("uri strip_prefix /uploads/covers", rendered)

    def test_prod_unchanged(self):
        rendered = self.manager._render(Target.PROD)
        self.assertNotIn("@covers path /uploads/covers/*", rendered)
        self.assertNotIn("var/storage/covers", rendered)


if __name__ == "__main__":
    unittest.main()
