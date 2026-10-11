from __future__ import annotations

import unittest

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target


class LabCaddyR320Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_config()
        cls.manager = CaddyManager(cls.config)

    def test_dev_unchanged(self):
        text = self.manager._render(Target.DEV)
        self.assertIn(":8502 {", text)
        self.assertIn("bind 127.0.0.1", text)
        self.assertIn("127.0.0.1:8602", text)
        self.assertNotIn("bind 0.0.0.0", text)
        self.assertNotIn(":8702 {", text)

    def test_prod_unchanged(self):
        text = self.manager._render(Target.PROD)
        self.assertIn(":8501 {", text)
        self.assertIn("bind 127.0.0.1", text)
        self.assertIn("127.0.0.1:8510", text)
        self.assertNotIn("bind 0.0.0.0", text)
        self.assertNotIn(":8702 {", text)

    def test_lab_additive_proxy(self):
        text = self.manager._render(Target.LAB)
        self.assertIn(":8702 {", text)
        self.assertIn("bind 0.0.0.0", text)
        self.assertIn("reverse_proxy 127.0.0.1:8701", text)
        self.assertIn("admin 127.0.0.1:2021", text)
        self.assertNotIn(":8501 {", text)
        self.assertNotIn(":8502 {", text)

    def test_lab_transport_remains_loopback(self):
        self.assertEqual(self.config.lab.backend_port, 8701)
        self.assertEqual(self.config.lab.public_port, 8702)
        self.assertEqual(self.config.lab_backend_url, "http://127.0.0.1:8701")

    def test_isolation_guards(self):
        for target in (Target.DEV, Target.PROD, Target.LAB):
            self.manager._validate_target_isolation(target)


if __name__ == "__main__":
    unittest.main()
