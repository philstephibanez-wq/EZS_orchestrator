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


@dataclass(frozen=True, slots=True)
class CaddyView:
    target: Target
    public_port: int
    upstream_port: int
    media_root: Path
    pid: int | None
    process_alive: bool
    http_alive: bool


class CaddyManager:
    def __init__(self, config: RuntimeConfig, caddy_exe: Path = Path(r"H:\Caddy\caddy.exe")) -> None:
        self.config = config
        self.caddy_exe = Path(caddy_exe)

    def _spec(self, target: Target):
        return self.config.dev if target is Target.DEV else self.config.prod

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
        return 2019 if target is Target.DEV else 2020

    def _upstream_port(self, target: Target) -> int:
        spec = self._spec(target)
        return int(spec.gateway_port) if target is Target.PROD and spec.gateway_port else int(spec.backend_port)

    def _media_root(self, target: Target) -> Path:
        return self._spec(target).root / "var" / "storage" / "stems"

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            import ctypes
            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                process_query_limited_information, False, int(pid)
            )
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
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

    def _write_metadata(self, target: Target, pid: int) -> None:
        payload = {
            "schema": "ezs.caddy-process.v1",
            "target": target.value,
            "pid": int(pid),
            "public_port": int(self._spec(target).public_port),
            "upstream_port": self._upstream_port(target),
            "media_root": str(self._media_root(target)),
            "config_path": str(self._config_path(target)),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        self._metadata_path(target).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _render(self, target: Target) -> str:
        spec = self._spec(target)
        media_root = self._media_root(target).as_posix()
        public_port = int(spec.public_port)
        upstream_port = self._upstream_port(target)
        admin_port = self._admin_port(target)
        return (
            "{\n"
            "    auto_https off\n"
            f"    admin 127.0.0.1:{admin_port}\n"
            "}\n\n"
            f"http://127.0.0.1:{public_port} {{\n"
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
            "    handle {\n"
            f"        reverse_proxy 127.0.0.1:{upstream_port}\n"
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
            return isinstance(code, int) and 100 <= code < 500

    def view(self, target: Target) -> CaddyView:
        meta = self._read_metadata(target)
        pid = int(meta.get("pid", 0) or 0) or None
        alive = self._pid_alive(pid)
        return CaddyView(
            target=target,
            public_port=int(self._spec(target).public_port),
            upstream_port=self._upstream_port(target),
            media_root=self._media_root(target),
            pid=pid,
            process_alive=alive,
            http_alive=self._http_alive(target) if alive else False,
        )

    def start(self, target: Target) -> CaddyView:
        current = self.view(target)
        if current.process_alive:
            return current

        if not self.caddy_exe.is_file():
            raise RuntimeError(f"caddy_executable_missing:{self.caddy_exe}")

        spec = self._spec(target)
        runtime_dir = self._runtime_dir(target)
        runtime_dir.mkdir(parents=True, exist_ok=True)

        media_root = self._media_root(target)
        if not media_root.is_dir():
            raise RuntimeError(f"caddy_media_root_missing:{target.value}:{media_root}")

        dev_root = self.config.dev.root.resolve()
        prod_root = self.config.prod.root.resolve()
        resolved_media = media_root.resolve()

        if target is Target.DEV:
            if resolved_media == prod_root or prod_root in resolved_media.parents:
                raise RuntimeError("caddy_cross_root_refused:dev->prod")
            if int(spec.public_port) == int(self.config.prod.public_port):
                raise RuntimeError("caddy_cross_port_refused:dev->prod")
        else:
            if resolved_media == dev_root or dev_root in resolved_media.parents:
                raise RuntimeError("caddy_cross_root_refused:prod->dev")
            if int(spec.public_port) == int(self.config.dev.public_port):
                raise RuntimeError("caddy_cross_port_refused:prod->dev")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if sock.connect_ex(("127.0.0.1", int(spec.public_port))) == 0:
                raise RuntimeError(
                    f"caddy_public_port_in_use:{target.value}:{spec.public_port}"
                )
        finally:
            sock.close()

        config_path = self._config_path(target)
        config_path.write_text(self._render(target), encoding="utf-8")

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
                + validate.stdout.replace("\r", " ").replace("\n", " ")[:800]
            )

        out = self._out_log(target).open("a", encoding="utf-8", errors="replace")
        err = self._err_log(target).open("a", encoding="utf-8", errors="replace")
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
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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
            f"caddy_start_failed:{target.value}:see {self._err_log(target)}"
        )
