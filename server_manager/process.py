from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    pid: int | None
    alive: bool
    owned: bool
    command_line: str | None


def pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    proc = subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            f"if (Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=WINDOWS_NO_WINDOW,
        check=False,
    )
    return proc.returncode == 0


def command_line(pid: int) -> str | None:
    if os.name != "nt":
        return None
    script = (
        f"$p=Get-CimInstance Win32_Process -Filter \"ProcessId = {int(pid)}\" "
        "-ErrorAction SilentlyContinue; if($p){[Console]::Out.Write($p.CommandLine)}"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=WINDOWS_NO_WINDOW,
        check=False,
    )
    value = proc.stdout.strip()
    return value or None


def listener_pid(port: int) -> int | None:
    if os.name != "nt":
        return None
    script = (
        f"$c=Get-NetTCPConnection -LocalPort {int(port)} -State Listen "
        "-ErrorAction SilentlyContinue | Select-Object -First 1; "
        "if($c){[Console]::Out.Write($c.OwningProcess)}"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="ascii",
        errors="ignore",
        creationflags=WINDOWS_NO_WINDOW,
        check=False,
    )
    try:
        value = int(proc.stdout.strip())
        return value if value > 0 else None
    except Exception:
        return None


def exact_php_server(pid: int, port: int, public_dir: Path) -> bool:
    cmd = command_line(pid)
    if not cmd:
        return False
    normalized = cmd.lower().replace('"', "")
    bind = f"-s 127.0.0.1:{int(port)}"
    root = f"-t {str(public_dir)}".lower()
    return bind in normalized and root in normalized


def http_alive(url: str, timeout: float = 0.8) -> bool:
    req = urllib.request.Request(
        url.rstrip("/") + "/fr/login",
        headers={"User-Agent": "EZS-Orchestrator/2"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return 200 <= int(response.status) < 500
    except urllib.error.HTTPError as exc:
        return 400 <= int(exc.code) < 500
    except Exception:
        return False


def stop_exact(pid: int, port: int, public_dir: Path, timeout: float = 8.0) -> None:
    if not exact_php_server(pid, port, public_dir):
        raise RuntimeError(
            f"STOP: PID {pid} is not the exact expected PHP server "
            f"for port {port} / docroot {public_dir}"
        )
    subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            f"Stop-Process -Id {int(pid)} -Force -ErrorAction Stop"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=WINDOWS_NO_WINDOW,
        check=True,
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return
        time.sleep(0.1)
    raise RuntimeError(f"PID {pid} did not stop")


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
