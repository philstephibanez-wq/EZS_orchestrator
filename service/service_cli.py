from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from contracts.target import Target
from .runner import PermanentRunner
from .singleton import ServiceSingletonBusy
from config.loader import load_runtime_config


WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def runtime_paths():
    config = load_runtime_config()
    service_dir = config.orchestrator_root / "runtime" / "service"
    service_dir.mkdir(parents=True, exist_ok=True)
    return (
        config,
        service_dir,
        service_dir / "service.json",
        service_dir / "heartbeat.json",
        service_dir / "stop.request",
        service_dir / "service.out.log",
        service_dir / "service.err.log",
    )


def _target_from_scope(scope: str) -> Target | None:
    if scope == "all":
        return None
    return Target(scope)


def run_foreground(scope: str, poll_seconds: float) -> int:
    try:
        return PermanentRunner(
            _target_from_scope(scope),
            poll_seconds=poll_seconds,
        ).run_forever()
    except ServiceSingletonBusy as exc:
        print(f"SERVICE_ALREADY_RUNNING: {exc}", file=sys.stderr)
        return 3


def start(scope: str, poll_seconds: float) -> int:
    config, service_dir, meta, heartbeat, stop_file, out_path, err_path = runtime_paths()
    stop_file.unlink(missing_ok=True)

    if meta.is_file():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            pid = int(data.get("pid") or 0)
        except Exception:
            pid = 0
        if pid > 0:
            print(f"service metadata already present pid={pid}; use status")
            return 3

    out = out_path.open("ab")
    err = err_path.open("ab")
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "service.service_cli",
                "run",
                "--target",
                scope,
                "--poll-seconds",
                str(poll_seconds),
            ],
            cwd=str(config.orchestrator_root),
            stdout=out,
            stderr=err,
            creationflags=WINDOWS_NO_WINDOW if os.name == "nt" else 0,
        )
    finally:
        out.close()
        err.close()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if meta.is_file():
            print(
                f"service_started target={scope} pid={proc.pid} "
                f"poll={poll_seconds}s"
            )
            return 0
        if proc.poll() is not None:
            print(
                f"service failed to start returncode={proc.returncode}",
                file=sys.stderr,
            )
            return proc.returncode or 2
        time.sleep(0.1)

    print("service start timeout: metadata not published", file=sys.stderr)
    return 2


def status() -> int:
    _config, _service_dir, meta, heartbeat, _stop, _out, _err = runtime_paths()
    if not meta.is_file():
        print("SERVICE: stopped")
        return 0

    try:
        m = json.loads(meta.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"SERVICE: metadata_error {exc}")
        return 2

    hb = {}
    if heartbeat.is_file():
        try:
            hb = json.loads(heartbeat.read_text(encoding="utf-8"))
        except Exception:
            hb = {}

    print(
        "SERVICE: "
        f"running pid={m.get('pid')} target={m.get('target')} "
        f"poll={m.get('poll_seconds')}s state={hb.get('state', 'unknown')} "
        f"heartbeat={hb.get('at', '-')}"
    )
    return 0


def stop(wait_seconds: float) -> int:
    _config, _service_dir, meta, _heartbeat, stop_file, _out, _err = runtime_paths()
    if not meta.is_file():
        print("SERVICE: already stopped")
        return 0

    stop_file.write_text("stop\n", encoding="ascii")
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if not meta.exists():
            print("SERVICE: stopped")
            return 0
        time.sleep(0.2)

    print(
        "SERVICE: stop requested but service still active; "
        "no forced termination performed",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    p = argparse.ArgumentParser(prog="EZS_orchestrator service")
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("start", "run"):
        sp = sub.add_parser(name)
        sp.add_argument(
            "--target",
            choices=("all", "dev", "prod"),
            required=True,
            help="all = one permanent service polling DEV and PROD",
        )
        sp.add_argument("--poll-seconds", type=float, default=2.0)

    sub.add_parser("status")

    sp_stop = sub.add_parser("stop")
    sp_stop.add_argument("--wait-seconds", type=float, default=15.0)

    args = p.parse_args()

    if args.command == "start":
        return start(args.target, args.poll_seconds)
    if args.command == "run":
        return run_foreground(args.target, args.poll_seconds)
    if args.command == "status":
        return status()
    if args.command == "stop":
        return stop(args.wait_seconds)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
