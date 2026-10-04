from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.target import Target
from server_manager.process import command_line, listener_pid, pid_alive

PROTOCOL = "ezscore.online-gateway.v3"


@dataclass(frozen=True, slots=True)
class GatewayView:
    target: Target
    root: Path
    port: int
    pid: int | None
    process_alive: bool
    http_alive: bool
    protocol: str | None
    maintenance: bool | None
    backend_host: str | None
    backend_port: int | None
    ownership: str


class GatewayManager:
    """Lifecycle of the neutral PROD HTTP gateway.

    This manager does not import or execute analysis code. PROD is the only
    supported target because DEV goes directly from Caddy :8502 to backend :8602.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.runtime = config.orchestrator_root / "runtime" / "gateway" / "prod"
        self.logs = config.orchestrator_root / "logs" / "gateway"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    @property
    def spec(self):
        return self.config.prod

    @property
    def root(self) -> Path:
        return self.spec.root

    @property
    def port(self) -> int:
        if not self.spec.gateway_port:
            raise RuntimeError("prod_gateway_port_missing")
        return int(self.spec.gateway_port)

    @property
    def config_path(self) -> Path:
        return self.root / "var" / "runtime" / "online-gateway.json"

    @property
    def metadata_path(self) -> Path:
        return self.runtime / "process.json"

    @property
    def pid_path(self) -> Path:
        return self.runtime / "gateway.pid"

    def _read_pid(self) -> int | None:
        try:
            value = int(self.pid_path.read_text(encoding="ascii").strip())
            return value if value > 0 else None
        except Exception:
            return None

    def _owned(self, pid: int | None) -> bool:
        if not pid or not pid_alive(pid):
            return False
        cmd = (command_line(pid) or "").lower().replace("/", "\\")
        root = str(self.root.resolve()).lower().replace("/", "\\")
        return (
            "gateway_manager.server" in cmd
            and root in cmd
            and "--port" in cmd
            and str(self.port) in cmd
        )

    def _status_payload(self) -> dict | None:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}/__ezscore_gateway_status",
                timeout=1.0,
            ) as response:
                if int(response.status) != 200:
                    return None
                data = json.loads(response.read().decode("utf-8"))
                return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _write_config(self, maintenance: bool) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "ezscore.online-gateway.v1",
            "maintenance": bool(maintenance),
            "backend_host": "127.0.0.1",
            "backend_port": int(self.spec.backend_port),
            "public_url": f"http://127.0.0.1:{self.spec.public_port}",
        }
        tmp = self.config_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.config_path)

    def view(self) -> GatewayView:
        listener = listener_pid(self.port)
        stored = self._read_pid()
        pid = listener or stored
        alive = pid_alive(pid)
        owned = self._owned(pid)
        payload = self._status_payload() if alive else None
        protocol = str(payload.get("protocol")) if payload else None
        http_ok = bool(payload and payload.get("ok") and protocol == PROTOCOL)
        if not pid:
            ownership = "stopped"
        elif owned:
            ownership = "owned" if stored == pid else "orphan_exact"
        else:
            ownership = "foreign"
        return GatewayView(
            target=Target.PROD,
            root=self.root,
            port=self.port,
            pid=pid,
            process_alive=alive,
            http_alive=http_ok,
            protocol=protocol,
            maintenance=bool(payload.get("maintenance")) if payload else None,
            backend_host=str(payload.get("backend_host")) if payload else None,
            backend_port=int(payload.get("backend_port")) if payload and payload.get("backend_port") else None,
            ownership=ownership,
        )

    def start(self, maintenance: bool = False) -> GatewayView:
        if self.root.resolve() != self.config.prod.root.resolve():
            raise RuntimeError("gateway_cross_root_refused")
        if self.root.resolve() == self.config.dev.root.resolve():
            raise RuntimeError("gateway_prod_root_equals_dev_root")

        self._write_config(maintenance)
        current = self.view()
        if current.process_alive:
            if current.ownership in {"owned", "orphan_exact"} and current.http_alive:
                if current.pid:
                    self.pid_path.write_text(str(current.pid), encoding="ascii")
                return self.view()
            raise RuntimeError(
                f"STOP: gateway port {self.port} occupied by non-owned or unhealthy process pid={current.pid}"
            )

        out = (self.logs / "prod.out.log").open("ab")
        err = (self.logs / "prod.err.log").open("ab")
        try:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gateway_manager.server",
                    "--root",
                    str(self.root),
                    "--port",
                    str(self.port),
                ],
                cwd=str(self.config.orchestrator_root),
                stdout=out,
                stderr=err,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
        finally:
            out.close()
            err.close()

        self.pid_path.write_text(str(proc.pid), encoding="ascii")
        self.metadata_path.write_text(
            json.dumps(
                {
                    "schema": "ezs.gateway-process.v1",
                    "target": "prod",
                    "root": str(self.root),
                    "port": self.port,
                    "pid": proc.pid,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            view = self.view()
            if view.http_alive and view.protocol == PROTOCOL:
                return view
            time.sleep(0.15)
        raise RuntimeError(f"gateway_start_failed:prod:{self.port}")

    def set_maintenance(self, enabled: bool) -> GatewayView:
        current = self.view()
        if not current.process_alive or current.ownership not in {"owned", "orphan_exact"}:
            raise RuntimeError("gateway_not_owned_or_stopped")
        self._write_config(bool(enabled))
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            view = self.view()
            if view.http_alive and view.maintenance is bool(enabled):
                return view
            time.sleep(0.1)
        raise RuntimeError("gateway_maintenance_state_not_observed")

    def stop(self) -> GatewayView:
        current = self.view()
        if not current.process_alive:
            self.pid_path.unlink(missing_ok=True)
            self.metadata_path.unlink(missing_ok=True)
            return self.view()
        if current.ownership not in {"owned", "orphan_exact"} or not current.pid:
            raise RuntimeError(f"STOP: refusing to terminate foreign gateway pid={current.pid}")

        os.kill(int(current.pid), signal.SIGTERM)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if not pid_alive(current.pid):
                break
            time.sleep(0.1)
        if pid_alive(current.pid):
            raise RuntimeError(f"gateway_stop_timeout:pid={current.pid}")
        self.pid_path.unlink(missing_ok=True)
        self.metadata_path.unlink(missing_ok=True)
        return self.view()
