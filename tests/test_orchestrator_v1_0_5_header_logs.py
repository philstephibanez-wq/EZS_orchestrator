from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
web = (root/"control_center"/"web.py").read_text(encoding="utf-8-sig")
ast.parse(web)

assert web.index('<header class="topbar">') < web.index('<div id="shell" class="shell">')
assert 'EZS</b> ORCHESTRATOR <span class="muted">V1.0</span>' in web
assert 'Control Center · 127.0.0.1:8700' in web
assert 'V1.0 · local' not in web
assert 'Control Center local' not in web

for needle in (
    'data-view="infrastructure"',
    'data-view="queues"',
    'data-view="logs"',
    'data-view="deployment"',
    'id="view-logs"',
):
    assert needle in web, needle

for route in (
    "/api/status", "/api/jobs", "/api/logs", "/api/logs/export",
    "/api/action", "/api/deployment/plan", "/api/deployment/apply",
):
    assert route in web, route

print("EZS_ORCHESTRATOR_V1_0_5_HEADER_LOGS_OK")
