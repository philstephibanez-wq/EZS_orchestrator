from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESS = (ROOT / "server_manager" / "process.py").read_text(encoding="utf-8")
MANAGER = (ROOT / "server_manager" / "manager.py").read_text(encoding="utf-8")


class ServerHealthProbeContract(unittest.TestCase):
    def test_http_probe_accepts_explicit_path(self):
        self.assertIn('def http_alive(url: str, timeout: float = 2.0, path: str = "/fr/login") -> bool:', PROCESS)
        self.assertIn('probe_path = path if path.startswith("/") else "/" + path', PROCESS)
        self.assertIn('url.rstrip("/") + probe_path', PROCESS)

    def test_lab_does_not_probe_nonexistent_login_route(self):
        self.assertIn('health_path = "/internal/analysis/desktop/jobs/queue" if target is Target.LAB else "/fr/login"', MANAGER)
        self.assertIn('http_alive(f"http://127.0.0.1:{spec.backend_port}", path=health_path)', MANAGER)


if __name__ == "__main__":
    unittest.main()
