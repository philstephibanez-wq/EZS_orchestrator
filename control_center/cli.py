from __future__ import annotations

import argparse

from config.loader import load_runtime_config
from contracts.target import Target
from server_manager.manager import ServerManager


def cmd_status() -> int:
    config = load_runtime_config()
    manager = ServerManager(config)

    for target in (Target.DEV, Target.PROD):
        view = manager.view(target)
        gateway = f" gateway={view.gateway_port}" if view.gateway_port else ""
        print(
            f"{target.value.upper()}: root={view.root} "
            f"env={view.app_env} backend={view.backend_port} "
            f"public={view.public_port}{gateway}"
        )

    print(f"Analysis Python: {config.analysis_python}")
    print(f"Analysis entrypoint: {config.analysis_entrypoint}")
    print(f"GPU slots: {config.gpu_slots}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZS_orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    args = parser.parse_args()

    if args.command == "status":
        return cmd_status()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
