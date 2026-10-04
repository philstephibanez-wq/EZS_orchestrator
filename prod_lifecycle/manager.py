from __future__ import annotations

from dataclasses import asdict, dataclass

from caddy_manager.manager import CaddyManager, CaddyView
from config.loader import RuntimeConfig
from contracts.target import Target
from gateway_manager.manager import GatewayManager, GatewayView
from runtime_guard.activity import analysis_execution_active
from server_manager.manager import ServerManager, ServerView


@dataclass(frozen=True, slots=True)
class ProdLifecycleView:
    backend: ServerView
    gateway: GatewayView
    caddy: CaddyView
    mode: str
    online: bool

    def as_dict(self) -> dict:
        return {
            "backend": asdict(self.backend),
            "gateway": asdict(self.gateway),
            "caddy": asdict(self.caddy),
            "mode": self.mode,
            "online": self.online,
        }


class ProdLifecycleManager:
    """Coordinates operational lifecycle of the physical PROD chain only.

    Cloudflare -> Caddy :8501 -> Gateway :8510 -> Symfony :8511
    """

    def __init__(
        self,
        config: RuntimeConfig,
        servers: ServerManager | None = None,
        gateway: GatewayManager | None = None,
        caddy: CaddyManager | None = None,
    ) -> None:
        self.config = config
        self.servers = servers or ServerManager(config)
        self.gateway = gateway or GatewayManager(config)
        self.caddy = caddy or CaddyManager(config)

    def _assert_topology(self) -> None:
        prod = self.config.prod
        dev = self.config.dev
        if prod.root.resolve() == dev.root.resolve():
            raise RuntimeError("prod_dev_root_collision")
        if int(prod.backend_port) != 8511:
            raise RuntimeError(f"unexpected_prod_backend_port:{prod.backend_port}")
        if int(prod.gateway_port or 0) != 8510:
            raise RuntimeError(f"unexpected_prod_gateway_port:{prod.gateway_port}")
        if int(prod.public_port) != 8501:
            raise RuntimeError(f"unexpected_prod_public_port:{prod.public_port}")

    def _guard_destructive(self, action: str) -> None:
        if analysis_execution_active(self.config.orchestrator_root / "runtime"):
            raise RuntimeError(f"STOP: analysis execution active; refusing PROD {action}")

    def view(self) -> ProdLifecycleView:
        self._assert_topology()
        backend = self.servers.view(Target.PROD, "prod")
        gateway = self.gateway.view()
        caddy = self.caddy.view(Target.PROD)
        mode = "maintenance" if gateway.maintenance is True else "normal"
        online = bool(
            backend.process_alive
            and backend.http_alive
            and backend.ownership in {"owned", "orphan_exact"}
            and gateway.process_alive
            and gateway.http_alive
            and gateway.ownership in {"owned", "orphan_exact"}
            and caddy.process_alive
            and caddy.http_alive
        )
        return ProdLifecycleView(backend, gateway, caddy, mode, online)

    def start(self, mode: str = "normal") -> ProdLifecycleView:
        self._assert_topology()
        requested = mode.lower()
        if requested not in {"normal", "maintenance"}:
            raise ValueError("prod_mode_must_be_normal_or_maintenance")

        self.servers.start(Target.PROD, "prod")
        self.gateway.start(maintenance=True)
        self.caddy.start(Target.PROD)
        self.gateway.set_maintenance(requested == "maintenance")
        return self.view()

    def restart(self) -> ProdLifecycleView:
        self._assert_topology()
        self._guard_destructive("restart")
        current = self.view()
        requested_mode = current.mode

        # Keep the public edge alive in maintenance while Symfony restarts.
        if current.gateway.process_alive and current.gateway.ownership in {"owned", "orphan_exact"}:
            self.gateway.set_maintenance(True)
        else:
            self.gateway.start(maintenance=True)
        if not current.caddy.process_alive:
            self.caddy.start(Target.PROD)

        self.servers.restart(Target.PROD, "prod")

        # Re-assert every layer: an unhealthy/missing layer is never silently ignored.
        if not self.gateway.view().http_alive:
            self.gateway.stop()
            self.gateway.start(maintenance=True)
        if not self.caddy.view(Target.PROD).http_alive:
            self.caddy.stop(Target.PROD)
            self.caddy.start(Target.PROD)

        self.gateway.set_maintenance(requested_mode == "maintenance")
        return self.view()

    def stop(self) -> ProdLifecycleView:
        self._assert_topology()
        self._guard_destructive("stop")
        gateway_view = self.gateway.view()
        if gateway_view.process_alive and gateway_view.ownership in {"owned", "orphan_exact"}:
            self.gateway.set_maintenance(True)
        self.caddy.stop(Target.PROD)
        self.gateway.stop()
        self.servers.stop(Target.PROD)
        return self.view()

    def set_maintenance(self, enabled: bool) -> ProdLifecycleView:
        self._assert_topology()
        current = self.view()
        if not current.backend.process_alive or not current.backend.http_alive:
            raise RuntimeError("prod_backend_not_online")
        if not current.gateway.process_alive:
            self.gateway.start(maintenance=enabled)
        if not current.caddy.process_alive:
            self.caddy.start(Target.PROD)
        self.gateway.set_maintenance(bool(enabled))
        return self.view()
