from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.server import ServerSpec
from contracts.target import Target
from .process import (
    atomic_json,
    command_line,
    exact_php_server,
    http_alive,
    listener_pid,
    pid_alive,
    read_json,
    stop_exact,
)

WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass(frozen=True, slots=True)
class ServerView:
    target: Target
    root: str
    app_env: str
    backend_port: int
    public_port: int
    gateway_port: int | None
    pid: int | None
    process_alive: bool
    http_alive: bool
    ownership: str


class ServerManager:
    """Physical server process manager only.

    No scheduler/job/analysis dependency is allowed here.
    """

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.runtime = config.orchestrator_root / "runtime" / "servers"
        self.logs = config.orchestrator_root / "logs" / "servers"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def spec(self, target: Target) -> ServerSpec:
        return self.config.dev if target is Target.DEV else self.config.prod

    def _meta_path(self, target: Target) -> Path:
        return self.runtime / f"{target.value}.json"

    def _pid_path(self, target: Target) -> Path:
        return self.runtime / f"{target.value}.pid"

    def _read_pid(self, target: Target) -> int | None:
        try:
            value = int(self._pid_path(target).read_text(encoding="ascii").strip())
            return value if value > 0 else None
        except Exception:
            return None

    def _expected_owned(self, target: Target, pid: int) -> bool:
        spec = self.spec(target)
        return exact_php_server(pid, spec.backend_port, spec.root / "public")

    def view(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        meta = read_json(self._meta_path(target))
        env = spec.validate_env(app_env or str(meta.get("environment") or spec.default_env))

        stored_pid = self._read_pid(target)
        listener = listener_pid(spec.backend_port)
        pid = listener or stored_pid
        alive = pid_alive(pid)

        if not pid:
            ownership = "stopped"
        elif self._expected_owned(target, pid):
            ownership = "owned" if stored_pid == pid else "orphan_exact"
        else:
            ownership = "foreign"

        return ServerView(
            target=target,
            root=str(spec.root),
            app_env=env,
            backend_port=spec.backend_port,
            public_port=spec.public_port,
            gateway_port=spec.gateway_port,
            pid=pid,
            process_alive=alive,
            http_alive=http_alive(f"http://127.0.0.1:{spec.backend_port}") if alive else False,
            ownership=ownership,
        )

    def start(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        env = spec.validate_env(app_env or spec.default_env)
        public = spec.root / "public"

        if not public.is_dir():
            raise RuntimeError(f"Public directory missing: {public}")

        existing = listener_pid(spec.backend_port)
        if existing:
            if not exact_php_server(existing, spec.backend_port, public):
                raise RuntimeError(
                    f"STOP: port {spec.backend_port} is occupied by PID {existing}, "
                    f"but not by exact target {target.value} docroot {public}"
                )
            # Safe adoption only for the same target exact docroot.
            self._pid_path(target).write_text(str(existing), encoding="ascii")
            atomic_json(self._meta_path(target), {
                "schema": "ezs.server-instance.v1",
                "target": target.value,
                "environment": env,
                "pid": existing,
                "backend_port": spec.backend_port,
                "root": str(spec.root),
                "adopted": True,
            })
            return self.view(target, env)

        php = "php"
        out_path = self.logs / f"{target.value}.out.log"
        err_path = self.logs / f"{target.value}.err.log"
        out = out_path.open("ab")
        err = err_path.open("ab")
        process_env = os.environ.copy()
        process_env["APP_ENV"] = env
        process_env["APP_DEBUG"] = "1" if env == "dev" else "0"
        process_env["EZSCORE_INSTANCE"] = target.value
        try:
            proc = subprocess.Popen(
                [php, "-S", f"127.0.0.1:{spec.backend_port}", "-t", str(public)],
                cwd=str(spec.root),
                env=process_env,
                stdout=out,
                stderr=err,
                creationflags=WINDOWS_NO_WINDOW if os.name == "nt" else 0,
            )
        finally:
            out.close()
            err.close()

        time.sleep(0.5)
        if proc.poll() is not None:
            raise RuntimeError(
                f"{target.value} PHP server exited immediately with code {proc.returncode}"
            )

        self._pid_path(target).write_text(str(proc.pid), encoding="ascii")
        atomic_json(self._meta_path(target), {
            "schema": "ezs.server-instance.v1",
            "target": target.value,
            "environment": env,
            "pid": proc.pid,
            "backend_port": spec.backend_port,
            "root": str(spec.root),
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
        return self.view(target, env)

    def stop(self, target: Target) -> ServerView:
        spec = self.spec(target)
        listener = listener_pid(spec.backend_port)
        if not listener:
            self._pid_path(target).unlink(missing_ok=True)
            self._meta_path(target).unlink(missing_ok=True)
            return self.view(target, spec.default_env)

        # Never stop based solely on port/PID.
        stop_exact(listener, spec.backend_port, spec.root / "public")
        self._pid_path(target).unlink(missing_ok=True)
        self._meta_path(target).unlink(missing_ok=True)
        return self.view(target, spec.default_env)

    def restart(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        env = spec.validate_env(app_env or spec.default_env)
        self.stop(target)
        return self.start(target, env)
