from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
TERMS = (ROOT / "docs" / "UI_TERMINOLOGY.md").read_text(encoding="utf-8")


class R327UiTerminologyContract(unittest.TestCase):
    def test_orchestrator_is_the_only_ui_name_for_8700(self):
        self.assertIn("Orchestrator · 127.0.0.1:8700", WEB)
        self.assertIn('data-log="control_center">Orchestrator</button>', WEB)
        self.assertIn('data-log="control_center_error">Orchestrator erreurs</button>', WEB)
        self.assertNotIn(">Control Center<", WEB)
        self.assertNotIn("Control Center · 127.0.0.1:8700", WEB)

    def test_server_vocabulary_replaces_backend_in_ui(self):
        for label in ("Serveur DEV", "Serveur PROD", "Serveur LAB"):
            self.assertIn(label, WEB)
        for action in ("Démarrer serveur", "Redémarrer serveur", "Arrêter serveur"):
            self.assertIn(action, WEB)
        self.assertNotIn(">Backend DEV<", WEB)
        self.assertNotIn(">Backend PROD<", WEB)
        self.assertNotIn(">Backend LAB<", WEB)
        self.assertNotIn(">Démarrer backend<", WEB)

    def test_infrastructure_labels_are_canonical(self):
        self.assertIn("<dt>URL serveur</dt>", WEB)
        self.assertIn("<dt>Propriété processus</dt>", WEB)
        self.assertIn("<dt>Passerelle :8510</dt>", WEB)
        self.assertIn("<dt>Répertoire</dt>", WEB)
        self.assertNotIn("<dt>Transport</dt>", WEB)
        self.assertNotIn("<dt>Transport interne</dt>", WEB)
        self.assertNotIn("<dt>Ownership</dt>", WEB)
        self.assertNotIn("<dt>Ownership backend</dt>", WEB)
        self.assertNotIn("<dt>Gateway :8510</dt>", WEB)

    def test_assistant_labels_are_unambiguous(self):
        for label in (
            "Version source",
            "Version déployée",
            "État déploiement",
            "Processus assistant XPS",
            "Déploiement assistant → XPS",
            "Déploiement DEV → PROD",
        ):
            self.assertIn(label, WEB)
        self.assertNotIn("<dt>Runtime XPS</dt>", WEB)
        self.assertNotIn("<dt>Source LAB</dt>", WEB)
        self.assertNotIn("<dt>Version XPS</dt>", WEB)

    def test_visible_runtime_states_are_french(self):
        self.assertIn('STOPPED:"ARRÊTÉ"', WEB)
        self.assertIn('ONLINE:"EN LIGNE"', WEB)
        self.assertIn('BUSY:"OCCUPÉ"', WEB)
        self.assertIn('STALE:"PÉRIMÉ"', WEB)
        self.assertIn('svc.running?"ACTIF":"ARRÊTÉ"', WEB)
        self.assertIn('"VÉRIFICATION"', WEB)
        self.assertIn('"HORS LIGNE"', WEB)

    def test_internal_contracts_are_not_renamed(self):
        # Internal payload/API identifiers remain stable.
        self.assertIn('d.server', WEB)
        self.assertIn('pl.backend', WEB)
        self.assertIn('pl.gateway', WEB)
        self.assertIn('d.transport', WEB)
        self.assertIn('ds.ownership', WEB)
        self.assertIn('data-log="control_center"', WEB)

    def test_canonical_terminology_document_exists(self):
        self.assertIn("Termes interdits dans les libellés UI", TERMS)
        self.assertIn("| Application de supervision sur 127.0.0.1:8700 | Orchestrator |", TERMS)
        self.assertIn("| Serveur applicatif DEV / PROD / LAB | Serveur |", TERMS)


if __name__ == "__main__":
    unittest.main()
