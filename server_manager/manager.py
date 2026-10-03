from __future__ import annotations

from dataclasses import dataclass

from config.loader import RuntimeConfig
from contracts.server import ServerSpec
from contracts.target import Target


@dataclass(frozen=True, slots=True)
class ServerView:
    target: Target
    root: str
    app_env: str
    backend_port: int
    public_port: int
    gateway_port: int | None


class ServerManager:
    """Server topology and invariants.

    R1 deliberately does not own process start/stop yet.
    Process control will be migrated behind this API in a later increment.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config

    def spec(self, target: Target) -> ServerSpec:
        return self.config.dev if target is Target.DEV else self.config.prod

    def view(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        env = spec.validate_env(app_env or spec.default_env)
        return ServerView(
            target=target,
            root=str(spec.root),
            app_env=env,
            backend_port=spec.backend_port,
            public_port=spec.public_port,
            gateway_port=spec.gateway_port,
        )
