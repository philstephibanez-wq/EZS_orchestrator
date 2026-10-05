from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/"deployment"/"manager.py").read_text(encoding="utf-8-sig")
ast.parse(src)

for needle in (
    "env_overrides: dict[str, str] | None = None",
    "child_env = os.environ.copy()",
    "child_env.update(env_overrides)",
    "env=child_env",
    '"environment": dict(env_overrides or {})',
    'prod_command_env = {"APP_ENV": "prod", "APP_DEBUG": "0"}',
    "env_overrides=prod_command_env",
):
    assert needle in src, needle

# All Symfony/Composer deployment commands must receive the production environment.
composer_idx = src.index('"composer-install"')
doctrine_idx = src.index('"doctrine-migrations"', composer_idx)
cache_idx = src.index('"cache-clear"', doctrine_idx)
for start, end in (
    (composer_idx, doctrine_idx),
    (doctrine_idx, cache_idx),
    (cache_idx, src.index("restarted = self.prod.restart()", cache_idx)),
):
    assert "env_overrides=prod_command_env" in src[start:end]

# Existing Windows .BAT support remains.
assert "def _windows_command_argv" in src
assert '".bat", ".cmd"' in src

print("EZS_ORCHESTRATOR_V1_0_7_5_PROD_ENV_OK")
