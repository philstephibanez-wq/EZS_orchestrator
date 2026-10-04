from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.target import Target
from .api import ApiClient


def read_env_local(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    path = root / ".env.local"
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


@dataclass(frozen=True, slots=True)
class TargetEndpoint:
    target: Target
    root: Path
    base_url: str
    token: str

    def client(self) -> ApiClient:
        if not self.token:
            raise RuntimeError(f"{self.target.value}: ANALYSIS_WORKER_TOKEN missing")
        return ApiClient(self.base_url, self.token)


class TargetRegistry:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def endpoint(self, target: Target) -> TargetEndpoint:
        if target is Target.DEV:
            root = self.config.dev.root
            override = os.environ.get("EZS_DEV_ANALYSIS_TOKEN")
        else:
            root = self.config.prod.root
            override = os.environ.get("EZS_PROD_ANALYSIS_TOKEN")

        url = self.config.transport_url_for(target)

        env = read_env_local(root)
        token = override or env.get("ANALYSIS_WORKER_TOKEN") or ""
        return TargetEndpoint(target, root, url, token)
