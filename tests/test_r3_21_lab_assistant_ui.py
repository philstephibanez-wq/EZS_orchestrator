from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
JOBS = (ROOT / "transport" / "jobs.py").read_text(encoding="utf-8")


class R321ALabAssistantUiContract(unittest.TestCase):
    def test_dev_contract_preserved(self):
        self.assertIn('<article class="card target dev"><h2>DEV</h2>', WEB)
        self.assertIn('data-action="dev-server-start"', WEB)
        self.assertIn('href="http://127.0.0.1:8502/fr/catalog"', WEB)

    def test_prod_contract_preserved(self):
        self.assertIn('<article class="card target prod"><h2>PROD · exploitation protégée</h2>', WEB)
        self.assertIn('data-action="prod-start"', WEB)
        self.assertIn('href="https://ezscore.logandplay.com/fr/catalog"', WEB)

    def test_lab_runtime_is_visible(self):
        self.assertIn("lab = self.servers.view(Target.LAB)", WEB)
        self.assertIn("lab_caddy = self.caddy.view(Target.LAB)", WEB)
        self.assertIn('<h2>LAB · expérimentation isolée</h2>', WEB)
        self.assertIn('id="labBackend"', WEB)
        self.assertIn('id="labCaddy"', WEB)
        self.assertIn('data-action="lab-caddy-start"', WEB)

    def test_assistant_inventory_is_read_only(self):
        self.assertIn("def distributed_workers(self, target: Target)", JOBS)
        self.assertIn("/internal/analysis/desktop/distributed/workers", JOBS)
        self.assertIn("def _distributed_workers(self) -> dict:", WEB)
        self.assertIn('<h2>EZStudioLab_assistant · nœuds distribués</h2>', WEB)
        self.assertIn('id="assistantWorkers"', WEB)

    def test_no_distributed_claim_or_execution_action_in_control_center(self):
        self.assertNotIn("/distributed/jobs/claim", WEB)
        self.assertNotIn('data-action="assistant-claim"', WEB)
        self.assertNotIn('data-action="assistant-run"', WEB)

    def test_lab_logs_visible(self):
        self.assertIn('data-log="lab_server_error"', WEB)
        self.assertIn('data-log="lab_caddy_error"', WEB)

    def test_lab_queue_remains_present(self):
        self.assertIn('<h2>Queue LAB</h2>', WEB)
        self.assertIn('renderQueue("labQueueCount","labQueueList",l.queue)', WEB)


if __name__ == "__main__":
    unittest.main()
