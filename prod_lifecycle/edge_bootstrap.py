"""Bootstraps the PROD maintenance edge; never launches a PHP application."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target
from gateway_manager.manager import GatewayManager


def requested_maintenance(config_path: Path) -> bool:
    """Fail closed on a missing, unreadable, or invalid gateway configuration."""
    try:
        data = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and type(data.get("maintenance")) is bool:
            return data["maintenance"]
    except (OSError, ValueError, UnicodeError):
        pass
    return True


def main() -> int:
    config = load_runtime_config()
    gateway = GatewayManager(config)
    caddy = CaddyManager(config)
    desired_maintenance = requested_maintenance(gateway.config_path)

    # A normal-mode restart needs a verified PHP replacement for the historical
    # HTTP backend. Never create a new php -S process or accidentally expose PROD.
    effective_maintenance = True
    if not desired_maintenance:
        print("PROD_NORMAL_RESTORE_BLOCKED_BACKEND_MIGRATION_PENDING", flush=True)

    # The existing gateway config doubles as a runtime file. When maintenance is
    # already live, this operation is idempotent and preserves maintenance=true.
    gw = gateway.start(maintenance=effective_maintenance)
    if not gw.process_alive or not gw.http_alive or gw.maintenance is not True:
        raise RuntimeError("PROD_GATEWAY_MAINTENANCE_NOT_READY")
    edge = caddy.start(Target.PROD)
    if not edge.process_alive or not edge.http_alive:
        raise RuntimeError("PROD_CADDY_NOT_READY")
    print(f"PROD_EDGE_MAINTENANCE_READY CADDY_PID={edge.pid} GATEWAY_PID={gw.pid}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"PROD_EDGE_START_FAILED: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
