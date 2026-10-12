from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.target import Target
from server_manager.process import command_line, exact_process, executable_path, listener_pid, process_metrics


@dataclass(frozen=True, slots=True)
class CaddyView:
    target: Target
    public_port: int
    upstream_port: int
    media_root: Path
    pid: int | None
    process_alive: bool
    http_alive: bool
    ownership: str = "stopped"
    executable_path: str | None = None
    command_line: str | None = None
    cpu_percent: float | None = None
    ram_mb: float | None = None


class CaddyManager:
    def __init__(self, config: RuntimeConfig, caddy_exe: Path = Path(r"H:\Caddy\caddy.exe")) -> None:
        self.config = config
        self.caddy_exe = Path(caddy_exe)

    def _spec(self, target: Target):
        if target is Target.DEV:
            return self.config.dev
        if target is Target.PROD:
            return self.config.prod
        if target is Target.LAB and self.config.lab is not None:
            return self.config.lab
        raise ValueError(f"Unsupported Caddy target: {target!r}")

    def _runtime_dir(self, target: Target) -> Path:
        return self.config.orchestrator_root / "runtime" / "caddy" / target.value

    def _metadata_path(self, target: Target) -> Path:
        return self._runtime_dir(target) / "process.json"

    def _config_path(self, target: Target) -> Path:
        return self._runtime_dir(target) / "Caddyfile"

    def _out_log(self, target: Target) -> Path:
        return self._runtime_dir(target) / "caddy.out.log"

    def _err_log(self, target: Target) -> Path:
        return self._runtime_dir(target) / "caddy.err.log"

    def _admin_port(self, target: Target) -> int:
        if target is Target.DEV:
            return 2019
        if target is Target.PROD:
            return 2020
        if target is Target.LAB:
            return 2021
        raise ValueError(f"Unsupported Caddy target: {target!r}")

    def _upstream_port(self, target: Target) -> int:
        spec = self._spec(target)
        return int(spec.gateway_port) if target is Target.PROD and spec.gateway_port else int(spec.backend_port)

    def _media_root(self, target: Target) -> Path:
        return self._spec(target).root / "var" / "storage" / "stems"

    def _cover_root(self, target: Target) -> Path:
        return self._spec(target).root / "var" / "storage" / "covers"

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            import ctypes
            q = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(q, False, int(pid))
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        except Exception:
            return False

    def _read_metadata(self, target: Target) -> dict:
        path = self._metadata_path(target)
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_metadata(
        self,
        target: Target,
        pid: int,
        *,
        adopted: bool = False,
    ) -> None:
        payload = {
            "schema": "ezs.caddy-process.v1",
            "target": target.value,
            "pid": int(pid),
            "public_port": int(self._spec(target).public_port),
            "upstream_port": self._upstream_port(target),
            "media_root": str(self._media_root(target)),
            "config_path": str(self._config_path(target)),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "adopted": bool(adopted),
        }
        self._metadata_path(target).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _render(self, target: Target) -> str:
        spec = self._spec(target)
        public_port = int(spec.public_port)
        upstream_port = self._upstream_port(target)
        admin_port = self._admin_port(target)

        if target is Target.LAB:
            return (
                "{\n"
                "    auto_https off\n"
                f"    admin 127.0.0.1:{admin_port}\n"
                "}\n\n"
                f":{public_port} {{\n"
                "    bind 0.0.0.0\n"
                f"    reverse_proxy 127.0.0.1:{upstream_port}\n"
                "}\n"
            )

        media_root = self._media_root(target).as_posix()
        cover_root = self._cover_root(target).as_posix()

        if target is Target.PROD:
            reverse_proxy = (
                f"        reverse_proxy 127.0.0.1:{upstream_port} {{\n"
                "            header_up X-Forwarded-Proto https\n"
                "            header_up X-Forwarded-Port 443\n"
                "            header_up X-Forwarded-Host {http.request.host}\n"
                "        }\n"
            )
            covers_block = ""
        else:
            reverse_proxy = f"        reverse_proxy 127.0.0.1:{upstream_port}\n"
            covers_block = (
                "    @covers path /uploads/covers/*\n"
                "    handle @covers {\n"
                f'        root * "{cover_root}"\n'
                "        uri strip_prefix /uploads/covers\n"
                "        header {\n"
                '            Cache-Control "public, max-age=86400"\n'
                "        }\n"
                "        file_server\n"
                "    }\n\n"
            )

        return (
            "{\n"
            "    auto_https off\n"
            f"    admin 127.0.0.1:{admin_port}\n"
            "}\n\n"
            f":{public_port} {{\n"
            "    bind 127.0.0.1\n"
            "    @media path /media/*\n"
            "    handle @media {\n"
            f"        forward_auth 127.0.0.1:{upstream_port} {{\n"
            "            uri /internal/media/auth\n"
            "        }\n\n"
            f'        root * "{media_root}"\n'
            "        uri strip_prefix /media\n"
            "        header {\n"
            '            Cache-Control "private, max-age=3600"\n'
            "        }\n"
            "        file_server\n"
            "    }\n\n"
            f"{covers_block}"
            "    handle {\n"
            f"{reverse_proxy}"
            "    }\n"
            "}\n"
        )

    def _http_alive(self, target: Target) -> bool:
        url = f"http://127.0.0.1:{self._spec(target).public_port}/"
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                return 100 <= int(response.status) < 500
        except Exception as exc:
            code = getattr(exc, "code", None)
            return isinstance(code, int) and 100 <= code < 600

    def _expected_owned(self, target: Target, pid: int) -> bool:
        return exact_process(
            pid,
            self.caddy_exe,
            (
                "run",
                "--config",
                str(self._config_path(target)),
                "--adapter",
                "caddyfile",
            ),
        )

    def view(self, target: Target) -> CaddyView:
        meta = self._read_metadata(target)
        stored = int(meta.get("pid", 0) or 0) or None
        listener = listener_pid(int(self._spec(target).public_port))
        pid = listener or stored
        alive = self._pid_alive(pid)
        if not pid:
            ownership = "stopped"
        elif self._expected_owned(target, pid):
            if stored != pid:
                ownership = "orphan_exact"
            elif bool(meta.get("adopted")):
                ownership = "adopted"
            else:
                ownership = "owned"
        else:
            ownership = "foreign"
        metrics = process_metrics(pid)
        return CaddyView(
            target=target,
            public_port=int(self._spec(target).public_port),
            upstream_port=self._upstream_port(target),
            media_root=self._media_root(target),
            pid=pid,
            process_alive=alive,
            http_alive=self._http_alive(target) if alive else False,
            ownership=ownership,
            executable_path=executable_path(pid),
            command_line=command_line(pid) if pid else None,
            cpu_percent=metrics.get("cpu_percent"),
            ram_mb=metrics.get("ram_mb"),
        )

    def adopt(self, target: Target) -> CaddyView:
        listener = listener_pid(int(self._spec(target).public_port))
        if not listener:
            raise RuntimeError(
                f"caddy_adopt_refused:no_listener:{target.value}"
            )
        if not self._expected_owned(target, listener):
            raise RuntimeError(
                f"caddy_adopt_refused:foreign_process:"
                f"{target.value}:pid={listener}"
            )
        self._write_metadata(target, listener, adopted=True)
        return self.view(target)

    def _validate_target_isolation(self, target: Target) -> None:
        spec = self._spec(target)
        if target is Target.DEV:
            if int(spec.public_port) == int(self.config.prod.public_port):
                raise RuntimeError("caddy_cross_port_refused:dev->prod")
            if self.config.lab is not None and int(spec.public_port) == int(self.config.lab.public_port):
                raise RuntimeError("caddy_cross_port_refused:dev->lab")
            return
        if target is Target.PROD:
            if int(spec.public_port) == int(self.config.dev.public_port):
                raise RuntimeError("caddy_cross_port_refused:prod->dev")
            if self.config.lab is not None and int(spec.public_port) == int(self.config.lab.public_port):
                raise RuntimeError("caddy_cross_port_refused:prod->lab")
            return
        if target is Target.LAB:
            if self.config.lab is None:
                raise RuntimeError("caddy_lab_missing")
            if int(spec.public_port) in {int(self.config.dev.public_port), int(self.config.prod.public_port)}:
                raise RuntimeError("caddy_lab_cross_port_refused")
            if int(spec.backend_port) in {int(self.config.dev.backend_port), int(self.config.prod.backend_port)}:
                raise RuntimeError("caddy_lab_cross_backend_refused")
            return
        raise ValueError(f"Unsupported Caddy target: {target!r}")

    def start(self, target: Target) -> CaddyView:
        current = self.view(target)
        if current.process_alive:
            if current.ownership == "orphan_exact":
                return self.adopt(target)
            if current.ownership in {"owned", "adopted"}:
                return current
            raise RuntimeError(
                f"caddy_start_refused:foreign_process:"
                f"{target.value}:pid={current.pid}"
            )
        if not self.caddy_exe.is_file():
            raise RuntimeError(
                f"caddy_executable_missing:{self.caddy_exe}"
            )
        spec = self._spec(target)
        runtime_dir = self._runtime_dir(target)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        if target is not Target.LAB:
            media_root = self._media_root(target)
            if not media_root.is_dir():
                raise RuntimeError(
                    f"caddy_media_root_missing:{target.value}:{media_root}"
                )
            if target is Target.DEV:
                self._cover_root(target).mkdir(
                    parents=True,
                    exist_ok=True,
                )
        self._validate_target_isolation(target)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if sock.connect_ex(
                ("127.0.0.1", int(spec.public_port))
            ) == 0:
                raise RuntimeError(
                    f"caddy_public_port_in_use:"
                    f"{target.value}:{spec.public_port}"
                )
        finally:
            sock.close()
        config_path = self._config_path(target)
        config_path.write_text(
            self._render(target),
            encoding="utf-8",
        )
        validate = subprocess.run(
            [
                str(self.caddy_exe),
                "validate",
                "--config",
                str(config_path),
                "--adapter",
                "caddyfile",
            ],
            cwd=str(self.config.orchestrator_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if validate.returncode != 0:
            raise RuntimeError(
                "caddy_validate_failed:"
                + validate.stdout.replace("\r", " ")
                .replace("\n", " ")[:800]
            )
        out = self._out_log(target).open(
            "a",
            encoding="utf-8",
            errors="replace",
        )
        err = self._err_log(target).open(
            "a",
            encoding="utf-8",
            errors="replace",
        )
        proc = subprocess.Popen(
            [
                str(self.caddy_exe),
                "run",
                "--config",
                str(config_path),
                "--adapter",
                "caddyfile",
            ],
            cwd=str(self.config.orchestrator_root),
            stdout=out,
            stderr=err,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
        )
        out.close()
        err.close()
        self._write_metadata(target, proc.pid)
        deadline = time.time() + 8.0
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if self._http_alive(target):
                return self.view(target)
            time.sleep(0.2)
        if proc.poll() is None:
            proc.terminate()
        raise RuntimeError(
            f"caddy_start_failed:{target.value}:"
            f"see {self._err_log(target)}"
        )

    def stop(self, target: Target) -> CaddyView:
        current = self.view(target)
        if not current.process_alive:
            self._metadata_path(target).unlink(missing_ok=True)
            return self.view(target)
        if current.ownership not in {
            "owned",
            "adopted",
            "orphan_exact",
        }:
            raise RuntimeError(
                f"caddy_stop_refused:foreign_process:"
                f"{target.value}:pid={current.pid}"
            )
        if not self.caddy_exe.is_file():
            raise RuntimeError(
                f"caddy_executable_missing:{self.caddy_exe}"
            )
        stopped = subprocess.run(
            [
                str(self.caddy_exe),
                "stop",
                "--address",
                f"127.0.0.1:{self._admin_port(target)}",
            ],
            cwd=str(self.config.orchestrator_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if stopped.returncode != 0:
            raise RuntimeError(
                "caddy_stop_failed:"
                + stopped.stdout.replace("\r", " ")
                .replace("\n", " ")[:800]
            )
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if not self._pid_alive(current.pid):
                break
            time.sleep(0.1)
        if self._pid_alive(current.pid):
            raise RuntimeError(
                f"caddy_stop_timeout:{target.value}:pid={current.pid}"
            )
        self._metadata_path(target).unlink(missing_ok=True)
        return self.view(target)

    def restart(self, target: Target) -> CaddyView:
        self.stop(target)
        return self.start(target)
