from __future__ import annotations

import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
web_path = root / "control_center" / "web.py"
manager_path = root / "deployment" / "manager.py"
runtime_path = root / "config" / "runtime.json"

web = web_path.read_text(encoding="utf-8-sig")
manager = manager_path.read_text(encoding="utf-8-sig")
runtime = json.loads(runtime_path.read_text(encoding="utf-8-sig"))

ast.parse(web, filename=str(web_path))
ast.parse(manager, filename=str(manager_path))

# Navigation V1.0.
for needle in (
    'data-view="infrastructure"',
    'data-view="queues"',
    'data-view="deployment"',
    'id="collapse"',
    "EZS Orchestrator V1.0",
):
    assert needle in web, needle

# Existing operator actions: non-regression.
for action in (
    "dev-server-start",
    "dev-server-stop",
    "dev-server-restart",
    "dev-caddy-start",
    "prod-start",
    "prod-stop",
    "prod-restart",
    "prod-maintenance-on",
    "prod-maintenance-off",
    "service-start-all",
    "service-stop",
    "logs-clear",
):
    assert action in web, action

# Existing APIs: non-regression.
for route in (
    "/api/status",
    "/api/jobs",
    "/api/logs",
    "/api/logs/export",
    "/api/action",
):
    assert route in web, route

# New deployment APIs.
for route in (
    "/api/deployment/plan",
    "/api/deployment/history",
    "/api/deployment/detail",
    "/api/deployment/apply",
):
    assert route in web, route

# Deployment safety.
low = manager.lower()
assert r"h:\ezscore_dev" in low
assert r"h:\ezscore" in low
assert "robocopy" not in low
assert "copytree" not in low
assert "git push" not in low
assert "protected_paths_changed" in manager
assert "analysis_execution_active" in manager
assert "sqlite3" in manager
assert '["git", "merge", "--ff-only", confirmed_commit]' in manager
assert "doctrine:migrations:migrate" in manager
assert "PROD maintenance is intentionally not cleared" in manager

# Explicit PHP executable for both targets.
assert runtime["servers"]["dev"]["web_php"] == r"H:\PHP\php-8.5-x64\php.exe"
assert runtime["servers"]["prod"]["web_php"] == r"H:\PHP\php-8.5-x64\php.exe"

print("EZS_ORCHESTRATOR_V1_0_CONTRACT_OK")
