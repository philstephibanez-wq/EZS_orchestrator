from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
web_path = root / "control_center" / "web.py"
src = web_path.read_text(encoding="utf-8-sig")
ast.parse(src, filename=str(web_path))

assert 'class="collapseRow"' in src
assert 'class="collapseBtn"' in src
assert '&lt;&lt;' in src
assert 'collapsed?">>":"<<"' in src
assert 'aria-label="Réduire le volet"' in src

# Badge must keep a fixed 34x34 footprint and never flex-shrink.
assert "width:34px;height:34px;min-width:34px;min-height:34px;flex:0 0 34px" in src

# Old bottom control must be gone.
assert 'class="sideFoot"' not in src
assert "☰" not in src

# V1.0 navigation still present: no functional regression.
for needle in (
    'data-view="infrastructure"',
    'data-view="queues"',
    'data-view="deployment"',
    "/api/status",
    "/api/jobs",
    "/api/deployment/plan",
    "/api/deployment/apply",
):
    assert needle in src, needle

print("EZS_ORCHESTRATOR_V1_0_3_SIDEBAR_OK")
