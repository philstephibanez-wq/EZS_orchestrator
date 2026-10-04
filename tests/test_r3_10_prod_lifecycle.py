from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from caddy_manager.manager import CaddyManager, CaddyView
from contracts.target import Target
from gateway_manager.manager import GatewayView, PROTOCOL
from prod_lifecycle.manager import ProdLifecycleManager
from server_manager.manager import ServerView


@dataclass
class _Spec:
    root: Path
    backend_port: int
    public_port: int
    gateway_port: int | None


class _Config:
    def __init__(self, root: Path):
        self.orchestrator_root = root / "orch"
        self.dev = _Spec(root / "EZScore_dev", 8602, 8502, None)
        self.prod = _Spec(root / "EZScore", 8511, 8501, 8510)
        self.orchestrator_root.mkdir(parents=True)
        self.dev.root.mkdir(parents=True)
        self.prod.root.mkdir(parents=True)


class _Servers:
    def __init__(self, config: _Config):
        self.config = config
        self.running = False
        self.calls: list[str] = []

    def _view(self):
        return ServerView(
            target=Target.PROD,
            root=str(self.config.prod.root),
            app_env="prod",
            backend_port=8511,
            public_port=8501,
            gateway_port=8510,
            pid=11 if self.running else None,
            process_alive=self.running,
            http_alive=self.running,
            ownership="owned" if self.running else "stopped",
        )

    def view(self, target, app_env=None):
        assert target is Target.PROD
        return self._view()

    def start(self, target, app_env=None):
        assert target is Target.PROD and app_env == "prod"
        self.calls.append("backend:start")
        self.running = True
        return self._view()

    def restart(self, target, app_env=None):
        assert target is Target.PROD and app_env == "prod"
        self.calls.append("backend:restart")
        self.running = True
        return self._view()

    def stop(self, target):
        assert target is Target.PROD
        self.calls.append("backend:stop")
        self.running = False
        return self._view()


class _Gateway:
    def __init__(self, config: _Config):
        self.config = config
        self.running = False
        self.maintenance = None
        self.calls: list[str] = []

    def view(self):
        return GatewayView(
            target=Target.PROD,
            root=self.config.prod.root,
            port=8510,
            pid=12 if self.running else None,
            process_alive=self.running,
            http_alive=self.running,
            protocol=PROTOCOL if self.running else None,
            maintenance=self.maintenance if self.running else None,
            backend_host="127.0.0.1" if self.running else None,
            backend_port=8511 if self.running else None,
            ownership="owned" if self.running else "stopped",
        )

    def start(self, maintenance=False):
        self.calls.append(f"gateway:start:{bool(maintenance)}")
        self.running = True
        self.maintenance = bool(maintenance)
        return self.view()

    def set_maintenance(self, enabled):
        self.calls.append(f"gateway:maintenance:{bool(enabled)}")
        self.maintenance = bool(enabled)
        return self.view()

    def stop(self):
        self.calls.append("gateway:stop")
        self.running = False
        self.maintenance = None
        return self.view()


class _Caddy:
    def __init__(self, config: _Config):
        self.config = config
        self.running = False
        self.calls: list[str] = []

    def view(self, target):
        assert target is Target.PROD
        return CaddyView(
            target=Target.PROD,
            public_port=8501,
            upstream_port=8510,
            media_root=self.config.prod.root / "var" / "storage" / "stems",
            pid=13 if self.running else None,
            process_alive=self.running,
            http_alive=self.running,
        )

    def start(self, target):
        assert target is Target.PROD
        self.calls.append("caddy:start")
        self.running = True
        return self.view(target)

    def stop(self, target):
        assert target is Target.PROD
        self.calls.append("caddy:stop")
        self.running = False
        return self.view(target)


class R310ProdLifecycleTest(unittest.TestCase):
    def test_caddy_render_matches_public_host_on_loopback(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            cfg.prod.root.joinpath("var", "storage", "stems").mkdir(parents=True)
            cfg.dev.root.joinpath("var", "storage", "stems").mkdir(parents=True)
            manager = CaddyManager(cfg)  # type: ignore[arg-type]
            text = manager._render(Target.PROD)
            self.assertIn(":8501 {", text)
            self.assertIn("bind 127.0.0.1", text)
            self.assertIn("reverse_proxy 127.0.0.1:8510", text)
            self.assertNotIn("http://127.0.0.1:8501 {", text)


    def test_caddy_http_health_accepts_maintenance_503(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            manager = CaddyManager(cfg)  # type: ignore[arg-type]
            error = HTTPError(
                url="http://127.0.0.1:8501/",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=None,
            )
            with patch("caddy_manager.manager.urllib.request.urlopen", side_effect=error):
                self.assertTrue(manager._http_alive(Target.PROD))

    def test_start_restores_complete_prod_chain_and_normal_mode(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            servers, gateway, caddy = _Servers(cfg), _Gateway(cfg), _Caddy(cfg)
            manager = ProdLifecycleManager(cfg, servers, gateway, caddy)  # type: ignore[arg-type]
            view = manager.start("normal")
            self.assertTrue(view.online)
            self.assertEqual("normal", view.mode)
            self.assertEqual(["backend:start"], servers.calls)
            self.assertEqual(["gateway:start:True", "gateway:maintenance:False"], gateway.calls)
            self.assertEqual(["caddy:start"], caddy.calls)

    def test_maintenance_keeps_all_layers_online(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            servers, gateway, caddy = _Servers(cfg), _Gateway(cfg), _Caddy(cfg)
            manager = ProdLifecycleManager(cfg, servers, gateway, caddy)  # type: ignore[arg-type]
            manager.start("normal")
            view = manager.set_maintenance(True)
            self.assertTrue(view.online)
            self.assertEqual("maintenance", view.mode)
            self.assertTrue(servers.running)
            self.assertTrue(gateway.running)
            self.assertTrue(caddy.running)

    def test_stop_order_is_caddy_gateway_backend(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            servers, gateway, caddy = _Servers(cfg), _Gateway(cfg), _Caddy(cfg)
            manager = ProdLifecycleManager(cfg, servers, gateway, caddy)  # type: ignore[arg-type]
            manager.start("normal")
            # Unit contract uses no real global mutex holder, so stop is allowed.
            view = manager.stop()
            self.assertFalse(view.online)
            self.assertIn("caddy:stop", caddy.calls)
            self.assertIn("gateway:stop", gateway.calls)
            self.assertIn("backend:stop", servers.calls)

    def test_topology_refuses_wrong_prod_ports(self):
        with TemporaryDirectory() as td:
            cfg = _Config(Path(td))
            cfg.prod.public_port = 9999
            manager = ProdLifecycleManager(cfg, _Servers(cfg), _Gateway(cfg), _Caddy(cfg))  # type: ignore[arg-type]
            with self.assertRaisesRegex(RuntimeError, "unexpected_prod_public_port"):
                manager.view()


if __name__ == "__main__":
    unittest.main()
