"""Read-only, fail-closed preflight for the PROD internal FastCGI facade."""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from config.loader import load_runtime_config
from prod_lifecycle.edge_bootstrap import requested_maintenance

CADDY_CONFIG = Path(__file__).resolve().parents[1] / "web/config/caddy/Caddyfile.prod-internal-candidate"
PORTS = (8511, 8512)


def listener_exists(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def preflight() -> dict:
    cfg = load_runtime_config()
    if cfg.prod.root.resolve() == cfg.dev.root.resolve():
        raise RuntimeError("PROD_DEV_ROOT_COLLISION")
    if cfg.prod.root != Path(r"H:\EZScore"):
        raise RuntimeError("PROD_ROOT_UNEXPECTED")
    if not (cfg.prod.root / "public" / "index.php").is_file():
        raise RuntimeError("PROD_ENTRYPOINT_MISSING")
    content = CADDY_CONFIG.read_text(encoding="utf-8")
    for marker in ("http://127.0.0.1:8511", "bind 127.0.0.1",
                   "root * H:/EZScore/public", "php_fastcgi 127.0.0.1:8512"):
        if marker not in content:
            raise RuntimeError("PROD_INTERNAL_CADDY_INVALID")
    result = {
        "schema": "ezs.prod_fastcgi_preflight.v1",
        "maintenance_requested": requested_maintenance(
            cfg.prod.root / "var/runtime/online-gateway.json"
        ),
        "port_8511_occupied": listener_exists(8511),
        "port_8512_occupied": listener_exists(8512),
        "candidate_only": True,
    }
    return result


def main() -> int:
    try:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"PROD_FASTCGI_PREFLIGHT_FAILED={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
