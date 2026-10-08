from __future__ import annotations
import ast
from pathlib import Path
root = Path(__file__).resolve().parents[1]
src = (root/"control_center"/"web.py").read_text(encoding="utf-8-sig")
ast.parse(src)

for needle in (
    'id="deployModalBackdrop"',
    'Confirmer le déploiement DEV → PROD',
    'Mettre en pause le worker d’analyse',
    'Passer PROD en maintenance',
    'Sauvegarder la base de données PROD',
    'Mettre à jour le code PROD vers la version DEV validée',
    'Vérifier que PROD répond correctement',
    'Aucune donnée métier DEV n’est copiée vers PROD.',
    'Déployer vers PROD',
    'function openDeploymentModal(fresh)',
    'const confirmed=await openDeploymentModal(fresh);',
    'if(!confirmed)return;',
):
    assert needle in src, needle

assert 'quiesce worker' not in src
assert 'confirm(msg)' not in src

for route in ("/api/deployment/plan", "/api/deployment/apply", "/api/deployment/history"):
    assert route in src, route

print("EZS_ORCHESTRATOR_V1_0_7_3_DEPLOY_MODAL_OK")
