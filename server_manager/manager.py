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
from runtime_guard.activity import analysis_execution_active
from .process import (
    atomic_json,
    command_line,
    exact_php_server,
    executable_path,
    http_alive,
    listener_pid,
    pid_alive,
    process_metrics,
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
    executable_path: str | None = None
    command_line: str | None = None
    cpu_percent: float | None = None
    ram_mb: float | None = None


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
        if target is Target.DEV:
            return self.config.dev
        if target is Target.PROD:
            return self.config.prod
        if target is Target.LAB and self.config.lab is not None:
            return self.config.lab
        raise ValueError(f"Unsupported server target: {target!r}")

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
        php_path = self.config.web_php_for(target)
        executable = php_path if php_path.is_absolute() else None
        return exact_php_server(
            pid, spec.backend_port, spec.root / "public", executable
        )

    def view(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        meta = read_json(self._meta_path(target))
        env = spec.validate_env(
            app_env or str(meta.get("environment") or spec.default_env)
        )
        stored_pid = self._read_pid(target)
        listener = listener_pid(spec.backend_port)
        pid = listener or (
            stored_pid if pid_alive(stored_pid) else None
        )
        alive = pid_alive(pid)

        if not pid:
            ownership = "stopped"
        elif self._expected_owned(target, pid):
            if stored_pid != pid:
                ownership = "orphan_exact"
            elif bool(meta.get("adopted")):
                ownership = "adopted"
            else:
                ownership = "owned"
        else:
            ownership = "foreign"

        health_path = "/home" if target is Target.LAB else "/fr/login"
        metrics = process_metrics(pid)
        return ServerView(
            target=target,
            root=str(spec.root),
            app_env=env,
            backend_port=spec.backend_port,
            public_port=spec.public_port,
            gateway_port=spec.gateway_port,
            pid=pid,
            process_alive=alive,
            http_alive=(
                http_alive(
                    f"http://127.0.0.1:{spec.backend_port}",
                    path=health_path,
                )
                if alive
                else False
            ),
            ownership=ownership,
            executable_path=executable_path(pid),
            command_line=command_line(pid) if pid else None,
            cpu_percent=metrics.get("cpu_percent"),
            ram_mb=metrics.get("ram_mb"),
        )

    def adopt(
        self,
        target: Target,
        app_env: str | None = None,
    ) -> ServerView:
        spec = self.spec(target)
        env = spec.validate_env(app_env or spec.default_env)
        listener = listener_pid(spec.backend_port)
        if not listener:
            raise RuntimeError(
                f"adopt_refused:no_listener:{target.value}:{spec.backend_port}"
            )
        if not self._expected_owned(target, listener):
            raise RuntimeError(
                f"adopt_refused:foreign_process:{target.value}:pid={listener}"
            )
        self._pid_path(target).write_text(str(listener), encoding="ascii")
        atomic_json(
            self._meta_path(target),
            {
                "schema": "ezs.server-instance.v1",
                "target": target.value,
                "environment": env,
                "pid": listener,
                "backend_port": spec.backend_port,
                "root": str(spec.root),
                "adopted": True,
                "adopted_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return self.view(target, env)

    def _clear_framework_cache(
        self,
        target: Target,
        env: str,
    ) -> None:
        # Clear disposable Symfony cache before DEV/LAB launch only.
        if target not in {Target.DEV, Target.LAB}:
            return

        spec = self.spec(target)
        console = spec.root / "bin" / "console"
        if not console.is_file():
            raise RuntimeError(
                f"symfony_console_missing:{target.value}:{console}"
            )

        php_path = self.config.web_php_for(target)
        if php_path.is_absolute() and not php_path.is_file():
            raise RuntimeError(
                f"PHP executable missing for {target.value}: {php_path}"
            )

        completed = subprocess.run(
            [
                str(php_path),
                str(console),
                "cache:clear",
                f"--env={env}",
                "--no-interaction",
            ],
            cwd=str(spec.root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if completed.returncode != 0:
            detail = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"rc={completed.returncode}"
            )
            raise RuntimeError(
                f"symfony_cache_clear_failed:{target.value}:{detail[:500]}"
            )

    def start(
        self,
        target: Target,
        app_env: str | None = None,
    ) -> ServerView:
        # Built-in PHP HTTP serving is forbidden across the EZS platform.
        # No implicit fallback: the owning FastCGI lifecycle must be used.
        raise RuntimeError("php_builtin_server_forbidden:use_caddy_fastcgi_lifecycle")

    def stop(self, target: Target) -> ServerView:
        spec = self.spec(target)
        if analysis_execution_active(
            self.config.orchestrator_root / "runtime"
        ):
            raise RuntimeError(
                f"STOP: analysis execution active; refusing to stop "
                f"{target.value} server"
            )
        listener = listener_pid(spec.backend_port)
        if not listener:
            self._pid_path(target).unlink(missing_ok=True)
            self._meta_path(target).unlink(missing_ok=True)
            return self.view(target, spec.default_env)

        php_path = self.config.web_php_for(target)
        executable = php_path if php_path.is_absolute() else None
        stop_exact(
            listener,
            spec.backend_port,
            spec.root / "public",
            executable=executable,
        )
        self._pid_path(target).unlink(missing_ok=True)
        self._meta_path(target).unlink(missing_ok=True)
        return self.view(target, spec.default_env)

    def restart(self, target: Target, app_env: str | None = None) -> ServerView:
        spec = self.spec(target)
        env = spec.validate_env(app_env or spec.default_env)
        self.stop(target)
        return self.start(target, env)
