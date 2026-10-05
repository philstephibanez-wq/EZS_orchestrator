from __future__ import annotations

import ctypes
import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar

WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_CACHE_TTL_SECONDS = 1.0
_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[str, int], tuple[float, object]] = {}
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    pid: int | None
    alive: bool
    owned: bool
    command_line: str | None


def _cached(kind: str, key: int, loader: Callable[[], T]) -> T:
    now = time.monotonic()
    cache_key = (kind, int(key))
    with _CACHE_LOCK:
        item = _CACHE.get(cache_key)
        if item and (now - item[0]) <= _CACHE_TTL_SECONDS:
            return item[1]  # type: ignore[return-value]
    value = loader()
    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.monotonic(), value)
    return value


def clear_process_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def _pid_alive_uncached(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    try:
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    except Exception:
        return False


def pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    return bool(_cached("pid", int(pid), lambda: _pid_alive_uncached(int(pid))))


def _command_line_uncached(pid: int) -> str | None:
    if os.name != "nt":
        return None
    script = (
        f'$p=Get-CimInstance Win32_Process -Filter "ProcessId = {int(pid)}" '
        "-ErrorAction SilentlyContinue; if($p){[Console]::Out.Write($p.CommandLine)}"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=WINDOWS_NO_WINDOW,
            check=False,
            timeout=3.0,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    value = proc.stdout.strip()
    return value or None


def command_line(pid: int) -> str | None:
    if pid <= 0:
        return None
    return _cached("cmd", int(pid), lambda: _command_line_uncached(int(pid)))


class _MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("dwState", ctypes.c_ulong),
        ("dwLocalAddr", ctypes.c_ulong),
        ("dwLocalPort", ctypes.c_ulong),
        ("dwRemoteAddr", ctypes.c_ulong),
        ("dwRemotePort", ctypes.c_ulong),
        ("dwOwningPid", ctypes.c_ulong),
    ]


def _listener_pid_uncached(port: int) -> int | None:
    if os.name != "nt":
        return None

    AF_INET = 2
    TCP_TABLE_OWNER_PID_LISTENER = 3
    ERROR_INSUFFICIENT_BUFFER = 122

    try:
        get_table = ctypes.windll.iphlpapi.GetExtendedTcpTable
        size = ctypes.c_ulong(0)
        rc = get_table(None, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0)
        if rc not in (0, ERROR_INSUFFICIENT_BUFFER) or size.value <= 4:
            return None
        buffer = ctypes.create_string_buffer(size.value)
        rc = get_table(buffer, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_LISTENER, 0)
        if rc != 0:
            return None
        count = ctypes.c_ulong.from_buffer_copy(buffer.raw[:4]).value
        row_size = ctypes.sizeof(_MIB_TCPROW_OWNER_PID)
        for index in range(int(count)):
            offset = 4 + index * row_size
            row = _MIB_TCPROW_OWNER_PID.from_buffer_copy(buffer.raw[offset:offset + row_size])
            raw_port = int(row.dwLocalPort) & 0xFFFF
            local_port = ((raw_port & 0xFF) << 8) | ((raw_port >> 8) & 0xFF)
            if local_port == int(port):
                pid = int(row.dwOwningPid)
                return pid if pid > 0 else None
    except Exception:
        return None
    return None
def listener_pid(port: int) -> int | None:
    if port <= 0:
        return None
    return _cached("port", int(port), lambda: _listener_pid_uncached(int(port)))


def exact_php_server(pid: int, port: int, public_dir: Path) -> bool:
    cmd = command_line(pid)
    if not cmd:
        return False
    normalized = cmd.lower().replace('"', "")
    bind = f"-s 127.0.0.1:{int(port)}"
    root = f"-t {str(public_dir)}".lower()
    return bind in normalized and root in normalized


def http_alive(url: str, timeout: float = 2.0) -> bool:
    req = urllib.request.Request(
        url.rstrip("/") + "/fr/login",
        headers={"User-Agent": "EZS-Orchestrator/3.14"},
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
        ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {int(pid)} -Force -ErrorAction Stop"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=WINDOWS_NO_WINDOW,
        check=True,
        timeout=5.0,
    )
    clear_process_cache()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        clear_process_cache()
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
