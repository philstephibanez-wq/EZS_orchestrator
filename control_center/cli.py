from __future__ import annotations

import argparse
import json

from config.loader import load_runtime_config
from contracts.target import Target
from orchestration.service import OrchestrationService
from prod_lifecycle.manager import ProdLifecycleManager
from server_manager.manager import ServerManager
from transport.jobs import JobTransport
from transport.targets import TargetRegistry


def parse_target(value: str) -> Target:
    return Target(value.lower())


def status() -> int:
    config = load_runtime_config()
    manager = ServerManager(config)
    prod = ProdLifecycleManager(config).view()
    dev = manager.view(Target.DEV)
    print(
        f"DEV: root={dev.root} env={dev.app_env} backend={dev.backend_port} public={dev.public_port} "
        f"pid={dev.pid or '-'} process={dev.process_alive} http={dev.http_alive} ownership={dev.ownership}"
    )
    print(
        f"PROD: root={prod.backend.root} env={prod.backend.app_env} backend={prod.backend.backend_port} "
        f"gateway={prod.gateway.port} public={prod.caddy.public_port} mode={prod.mode} online={prod.online} "
        f"backend_pid={prod.backend.pid or '-'} gateway_pid={prod.gateway.pid or '-'} caddy_pid={prod.caddy.pid or '-'}"
    )
    print(f"DEV Analysis Python: {config.analysis_python_for(Target.DEV)}")
    print(f"PROD Analysis Python: {config.analysis_python_for(Target.PROD)}")
    print(f"DEV Transport: {config.transport_url_for(Target.DEV)}")
    print(f"PROD Transport: {config.transport_url_for(Target.PROD)}")
    print(f"Analysis entrypoint: {config.analysis_entrypoint}")
    print(f"GPU slots: {config.gpu_slots}")
    return 0


def queue_status(target: Target | None) -> int:
    config = load_runtime_config()
    transport = JobTransport(TargetRegistry(config))
    targets = (target,) if target is not None else (Target.DEV, Target.PROD)
    failed = False
    for item in targets:
        try:
            jobs = transport.queue(item)
            print(f"{item.value.upper()}: {len(jobs)} job(s)")
            for job in jobs[:10]:
                print("  " + json.dumps(job, ensure_ascii=False))
        except Exception as exc:
            failed = True
            print(f"{item.value.upper()}: ERROR {exc}")
    return 1 if failed else 0


def run_once(target: Target) -> int:
    config = load_runtime_config()
    service = OrchestrationService(config)
    outcome = service.run_once(target, on_output=lambda line: print(line, flush=True))
    if outcome is None:
        print(f"No queued job for target={target.value}.")
        return 0
    print(f"job_id={outcome.job_id} target={outcome.target.value} returncode={outcome.returncode}")
    return 0 if outcome.returncode == 0 else outcome.returncode


def server_action(action: str, target_value: str, env: str | None) -> int:
    config = load_runtime_config()
    item = parse_target(target_value)
    if item is Target.PROD:
        raise RuntimeError("Use prod-start/prod-stop/prod-restart for complete PROD chain lifecycle.")
    manager = ServerManager(config)
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


def prod_action(action: str) -> int:
    manager = ProdLifecycleManager(load_runtime_config())
    if action == "start":
        view = manager.start("normal")
    elif action == "stop":
        view = manager.stop()
    elif action == "restart":
        view = manager.restart()
    elif action == "maintenance-on":
        view = manager.set_maintenance(True)
    elif action == "maintenance-off":
        view = manager.set_maintenance(False)
    else:
        raise ValueError(action)
    print(view)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZS_orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("health")

    queue_parser = sub.add_parser("queue")
    queue_parser.add_argument("--target", choices=("dev", "prod"), default=None)

    run_parser = sub.add_parser("run-once")
    run_parser.add_argument("--target", choices=("dev", "prod"), required=True)

    for name in ("server-start", "server-stop", "server-restart"):
        p = sub.add_parser(name)
        p.add_argument("target", choices=("dev", "prod"))
        if name != "server-stop":
            p.add_argument("--env", choices=("dev", "prod"), default=None)

    for name in ("prod-start", "prod-stop", "prod-restart", "prod-maintenance-on", "prod-maintenance-off"):
        sub.add_parser(name)

    args = parser.parse_args()
    if args.command in {"status", "health"}:
        return status()
    if args.command == "queue":
        return queue_status(parse_target(args.target) if args.target else None)
    if args.command == "run-once":
        return run_once(parse_target(args.target))
    if args.command == "server-start":
        return server_action("start", args.target, args.env)
    if args.command == "server-stop":
        return server_action("stop", args.target, None)
    if args.command == "server-restart":
        return server_action("restart", args.target, args.env)
    if args.command.startswith("prod-"):
        return prod_action(args.command.removeprefix("prod-").replace("maintenance-", "maintenance-"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
