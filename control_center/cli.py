from __future__ import annotations

import argparse
import json

from config.loader import load_runtime_config
from contracts.target import Target
from server_manager.manager import ServerManager
from transport.jobs import JobTransport
from transport.targets import TargetRegistry


def target(value: str) -> Target:
    return Target(value.lower())


def status() -> int:
    config = load_runtime_config()
    manager = ServerManager(config)
    for item in (Target.DEV, Target.PROD):
        view = manager.view(item)
        print(
            f"{item.value.upper()}: root={view.root} env={view.app_env} "
            f"backend={view.backend_port} public={view.public_port} "
            f"pid={view.pid or '-'} process={view.process_alive} "
            f"http={view.http_alive} ownership={view.ownership}"
        )
    print(f"Analysis Python: {config.analysis_python}")
    print(f"Analysis entrypoint: {config.analysis_entrypoint}")
    print(f"GPU slots: {config.gpu_slots}")
    return 0


def health() -> int:
    return status()


def queue_status() -> int:
    config = load_runtime_config()
    transport = JobTransport(TargetRegistry(config))
    failed = False
    for item in (Target.DEV, Target.PROD):
        try:
            jobs = transport.queue(item)
            print(f"{item.value.upper()}: {len(jobs)} job(s)")
            for job in jobs[:10]:
                print("  " + json.dumps(job, ensure_ascii=False))
        except Exception as exc:
            failed = True
            print(f"{item.value.upper()}: ERROR {exc}")
    return 1 if failed else 0


def server_action(action: str, target_value: str, env: str | None) -> int:
    config = load_runtime_config()
    manager = ServerManager(config)
    item = target(target_value)
    if action == "start":
        view = manager.start(item, env)
    elif action == "stop":
        view = manager.stop(item)
    elif action == "restart":
        view = manager.restart(item, env)
    else:
        raise ValueError(action)
    print(view)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZS_orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("health")
    sub.add_parser("queue")

    for name in ("server-start", "server-stop", "server-restart"):
        p = sub.add_parser(name)
        p.add_argument("target", choices=("dev", "prod"))
        if name != "server-stop":
            p.add_argument("--env", choices=("dev", "prod"), default=None)

    args = parser.parse_args()
    if args.command == "status":
        return status()
    if args.command == "health":
        return health()
    if args.command == "queue":
        return queue_status()
    if args.command == "server-start":
        return server_action("start", args.target, args.env)
    if args.command == "server-stop":
        return server_action("stop", args.target, None)
    if args.command == "server-restart":
        return server_action("restart", args.target, args.env)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
