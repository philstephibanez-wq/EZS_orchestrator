from __future__ import annotations

import argparse

from config.loader import load_runtime_config
from contracts.target import Target
from .manager import CaddyManager


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZS_orchestrator.caddy")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "start"):
        p = sub.add_parser(name)
        p.add_argument("--target", choices=("dev", "prod"), required=True)

    args = parser.parse_args()
    target = Target(args.target)
    manager = CaddyManager(load_runtime_config())
    view = manager.start(target) if args.command == "start" else manager.view(target)

    print(
        f"CADDY {view.target.value.upper()}: "
        f"public={view.public_port} upstream={view.upstream_port} "
        f"media_root={view.media_root} pid={view.pid or '-'} "
        f"process={view.process_alive} http={view.http_alive}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
