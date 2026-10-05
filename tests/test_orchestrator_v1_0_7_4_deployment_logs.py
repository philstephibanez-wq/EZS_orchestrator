from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/"control_center"/"web.py").read_text(encoding="utf-8-sig")
ast.parse(src)

for needle in (
    'data-log="deployments">Déploiements</button>',
    'currentLog==="deployments"',
    '"/api/deployment/history"',
    '/api/deployment/detail?id=',
    'HISTORIQUE DES DÉPLOIEMENTS',
    'DERNIER DÉPLOIEMENT — JOURNAL DÉTAILLÉ',
    'journal d’audit',
    '$("clearLogs").disabled=currentLog==="deployments";',
):
    assert needle in src, needle

# Existing log categories and deployment page remain.
for needle in (
    'data-log="service"',
    'data-log="control_center"',
    'data-log="prod_server_error"',
    'id="view-deployment"',
    'id="deployHistory"',
    'id="deployLog"',
):
    assert needle in src, needle

# No backend contract changes.
for route in (
    "/api/logs",
    "/api/logs/export",
    "/api/deployment/history",
    "/api/deployment/detail",
    "/api/deployment/apply",
):
    assert route in src, route

print("EZS_ORCHESTRATOR_V1_0_7_4_DEPLOYMENT_LOGS_OK")
