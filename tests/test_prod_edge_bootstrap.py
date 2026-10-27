import ast
import unittest
from pathlib import Path

from prod_lifecycle.edge_bootstrap import requested_maintenance

ROOT = Path(__file__).resolve().parents[1]


class ProdEdgeBootstrapContract(unittest.TestCase):
    def test_fail_closed_modes(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            path = Path(folder) / "gateway.json"
            self.assertTrue(requested_maintenance(path))
            for payload, expected in [('{"maintenance":true}', True),
                                      ('{"maintenance":false}', False),
                                      ('{"maintenance":"false"}', True),
                                      ('{"maintenance":null}', True),
                                      ('broken', True)]:
                path.write_text(payload, encoding="utf-8")
                self.assertIs(requested_maintenance(path), expected)

    def test_launcher_does_not_start_php_http(self):
        source = (ROOT / "prod_lifecycle" / "edge_bootstrap.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("servers.start(", source)
        self.assertNotIn("ProdLifecycleManager.start(", source)
        self.assertIn("effective_maintenance = True", source)
        launcher = (ROOT / "scripts" / "start.cmd").read_text(encoding="utf-8")
        self.assertIn("prod-edge-start.py", launcher)
        self.assertIn("if errorlevel 1 exit /b", launcher)
        entry = (ROOT / "scripts" / "prod-edge-start.py").read_text(encoding="utf-8")
        self.assertIn("sys.path.insert(0, str(ROOT))", entry)


if __name__ == "__main__":
    unittest.main()
