from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
web_path = root / "control_center" / "web.py"
src = web_path.read_text(encoding="utf-8-sig")
ast.parse(src, filename=str(web_path))

for needle in (
    'class="appHeader"',
    'class="appHeaderMark"',
    'class="viewContext"',
    'id="globalState" class="globalBadge"',
    'id="headerRefresh"',
    'Control Center local · 127.0.0.1:8700',
    'globalBadge.className="globalBadge "+(analysisActive?"busy":"")',
):
    assert needle in src, needle

# Sidebar + 3 views preserved.
for needle in (
    'data-view="infrastructure"',
    'data-view="queues"',
    'data-view="deployment"',
    'id="collapse"',
):
    assert needle in src, needle

# Functional API surface preserved.
for route in (
    "/api/status",
    "/api/jobs",
    "/api/logs",
    "/api/logs/export",
    "/api/action",
    "/api/deployment/plan",
    "/api/deployment/apply",
):
    assert route in src, route

print("EZS_ORCHESTRATOR_V1_0_4_HEADER_OK")
