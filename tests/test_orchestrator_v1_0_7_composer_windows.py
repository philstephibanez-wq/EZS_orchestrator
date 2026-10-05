from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/"deployment"/"manager.py").read_text(encoding="utf-8-sig")
ast.parse(src)

for needle in (
    "def _windows_command_argv",
    '".bat", ".cmd"',
    "subprocess.list2cmdline(argv)",
    '"/d", "/s", "/c"',
    "effective_argv = DeploymentManager._windows_command_argv(argv)",
):
    assert needle in src, needle

# Deployment contract remains.
for needle in (
    "GIT_FF_ONLY",
    "COMPOSER_INSTALL",
    "DOCTRINE_MIGRATIONS",
    "CACHE_CLEAR",
    "PROD_RESTART",
    "HEALTH_CHECK",
):
    assert needle in src, needle

print("EZS_ORCHESTRATOR_V1_0_7_COMPOSER_WINDOWS_OK")
