from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESS = (ROOT / "server_manager/process.py").read_text(encoding="utf-8")
SERVER = (ROOT / "server_manager/manager.py").read_text(encoding="utf-8")
CADDY = (ROOT / "caddy_manager/manager.py").read_text(encoding="utf-8")
GATEWAY = (ROOT / "gateway_manager/manager.py").read_text(encoding="utf-8")
WEB = (ROOT / "control_center/web.py").read_text(encoding="utf-8")
RUNNER = (ROOT / "service/runner.py").read_text(encoding="utf-8")
SINGLETON = (ROOT / "control_center/singleton.py").read_text(encoding="utf-8")


class Contract(unittest.TestCase):
    def test_control_center_singleton(self):
        self.assertIn(
            "Global\\EZS_orchestrator_control_center_v1",
            SINGLETON,
        )
        self.assertIn(
            "singleton.acquire(args.port)",
            WEB,
        )

    def test_strong_identity_and_adoption(self):
        self.assertIn(
            "QueryFullProcessImageNameW",
            PROCESS,
        )
        self.assertIn("def exact_process(", PROCESS)
        self.assertIn("def adopt(", SERVER)
        self.assertIn(
            "caddy_adopt_refused:foreign_process",
            CADDY,
        )
        self.assertIn(
            "gateway_adopt_refused",
            GATEWAY,
        )
        for text in (SERVER, CADDY, GATEWAY):
            self.assertIn("orphan_exact", text)
            self.assertIn("adopted", text)
            self.assertIn("foreign", text)

    def test_metrics_incidents_and_circuit(self):
        self.assertIn("def process_metrics(", PROCESS)
        self.assertIn('id="incidentPanel"', WEB)
        self.assertIn("/api/incidents/ack", WEB)
        self.assertIn("data-incident-log", WEB)
        self.assertIn("LabCircuitBreaker", RUNNER)
        self.assertIn("threshold=3", RUNNER)

    def test_zero_global_kill(self):
        all_text = (
            SERVER + CADDY + GATEWAY + WEB
        ).lower()
        self.assertNotIn(
            "get-process php | stop-process",
            all_text,
        )
        self.assertNotIn(
            "get-process python | stop-process",
            all_text,
        )
        self.assertNotIn(
            "get-process caddy | stop-process",
            all_text,
        )


if __name__ == "__main__":
    unittest.main()
