from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/"control_center"/"web.py").read_text(encoding="utf-8-sig")
ast.parse(src)

for needle in (
    "let deploymentRefreshRunning=false;",
    'refreshBtn.textContent="Analyse…";',
    '$("deployDecision").textContent="ANALYSE EN COURS…";',
    'Préflight DEV → PROD en cours',
    'Préflight terminé : déploiement possible.',
    'refreshBtn.disabled=false;',
):
    assert needle in src, needle

for route in (
    "/api/deployment/plan",
    "/api/deployment/history",
    "/api/deployment/apply",
):
    assert route in src, route

print("EZS_ORCHESTRATOR_V1_0_7_2_DEPLOY_REFRESH_FEEDBACK_OK")
