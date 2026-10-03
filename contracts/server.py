from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .target import Target


@dataclass(frozen=True, slots=True)
class ServerSpec:
    target: Target
    root: Path
    backend_port: int
    public_port: int
    allowed_envs: tuple[str, ...]
    default_env: str
    gateway_port: int | None = None

    def validate_env(self, app_env: str) -> str:
        value = app_env.lower()
        if value not in self.allowed_envs:
            raise ValueError(
                f"{self.target.value}: APP_ENV={value} forbidden; "
                f"allowed={self.allowed_envs}"
            )
        return value
