from __future__ import annotations

import unittest

from config.loader import load_runtime_config
from contracts.target import Target
from transport.targets import TargetRegistry


class R34bInternalTransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_config()

    def test_dev_transport_is_internal_backend(self):
        self.assertEqual(self.config.transport_url_for(Target.DEV), "http://127.0.0.1:8602")

    def test_prod_transport_is_internal_backend(self):
        self.assertEqual(self.config.transport_url_for(Target.PROD), "http://127.0.0.1:8511")

    def test_registry_uses_backend_not_public_port(self):
        registry = TargetRegistry(self.config)
        dev = registry.endpoint(Target.DEV)
        prod = registry.endpoint(Target.PROD)
        self.assertEqual(dev.base_url, "http://127.0.0.1:8602")
        self.assertEqual(prod.base_url, "http://127.0.0.1:8511")
        self.assertNotEqual(dev.base_url, "http://127.0.0.1:8502")
        self.assertNotEqual(prod.base_url, "http://127.0.0.1:8501")


if __name__ == "__main__":
    unittest.main()
