from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for rel in (
    "control_center/web.py",
    "deployment/manager.py",
    "deployment/__init__.py",
):
    path = root / rel
    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

runtime = json.loads((root / "config/runtime.json").read_text(encoding="utf-8-sig"))
assert runtime["servers"]["prod"]["web_php"] == r"H:\PHP\php-8.5-x64\php.exe"

sys.path.insert(0, str(root))
from deployment import DeploymentManager, DeploymentPlan, DeploymentPreflight
assert DeploymentPreflight is DeploymentPlan
assert DeploymentManager.__name__ == "DeploymentManager"

web = (root / "control_center/web.py").read_text(encoding="utf-8-sig")
for needle in (
    'data-view="infrastructure"',
    'data-view="queues"',
    'data-view="deployment"',
    'id="collapse"',
    "EZS Orchestrator V1.0",
):
    assert needle in web, needle

print("EZS_ORCHESTRATOR_V1_0_2_FULL_OK")
