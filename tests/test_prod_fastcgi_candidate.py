import ast
import unittest
from pathlib import Path

from prod_lifecycle.fastcgi_preflight import CADDY_CONFIG, PORTS

ROOT = Path(__file__).resolve().parents[1]


class ProdFastcgiCandidateTest(unittest.TestCase):
    def test_isolated_candidate(self):
        text = CADDY_CONFIG.read_text(encoding="utf-8")
        for value in ("127.0.0.1:8511", "127.0.0.1:8512", "bind 127.0.0.1", "root * H:/EZScore/public"):
            self.assertIn(value, text)
        self.assertNotIn("8501", text)
        self.assertNotIn("8502", text)
        self.assertNotIn("8790", text)
        self.assertEqual(PORTS, (8511, 8512))

    def test_runtime_is_not_activated(self):
        source = (ROOT / "prod_lifecycle/fastcgi_preflight.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("Popen(", source)
        self.assertNotIn("Start-Process", source)
        self.assertNotIn("set_maintenance(False)", source)
        start = (ROOT / "scripts/start.cmd").read_text(encoding="utf-8")
        self.assertNotIn("fastcgi_preflight", start)


if __name__ == "__main__":
    unittest.main()
