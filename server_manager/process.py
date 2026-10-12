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


def _executable_path_uncached(pid: int) -> str | None:
    if os.name != "nt":
        return None
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return None
        try:
            size = ctypes.c_ulong(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None
            return buffer.value or None
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return None


def executable_path(pid: int | None) -> str | None:
    if not pid or pid <= 0:
        return None
    return _cached("exe", int(pid), lambda: _executable_path_uncached(int(pid)))


_METRICS_LOCK = threading.Lock()
_METRICS_HISTORY: dict[int, tuple[float, float]] = {}


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong)]


class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def _filetime_seconds(value: _FILETIME) -> float:
    raw = (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)
    return raw / 10_000_000.0


def _process_resource_sample(pid: int) -> tuple[float, float] | None:
    if os.name != "nt":
        return None
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_VM_READ = 0x0010
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, int(pid))
        if not handle:
            return None
        try:
            creation = _FILETIME()
            exit_time = _FILETIME()
            kernel = _FILETIME()
            user = _FILETIME()
            if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
                return None
            counters = _PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(counters)
            if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return None
            cpu_seconds = _filetime_seconds(kernel) + _filetime_seconds(user)
            ram_mb = float(counters.WorkingSetSize) / (1024.0 * 1024.0)
            return cpu_seconds, ram_mb
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return None


def process_metrics(pid: int | None) -> dict:
    if not pid or not pid_alive(pid):
        return {"cpu_percent": None, "ram_mb": None}
    sample = _process_resource_sample(int(pid))
    if sample is None:
        return {"cpu_percent": None, "ram_mb": None}
    cpu_seconds, ram_mb = sample
    now = time.monotonic()
    cpu_percent = 0.0
    with _METRICS_LOCK:
        previous = _METRICS_HISTORY.get(int(pid))
        _METRICS_HISTORY[int(pid)] = (now, cpu_seconds)
    if previous is not None:
        elapsed = now - previous[0]
        cpu_delta = max(0.0, cpu_seconds - previous[1])
        if elapsed > 0:
            cpu_percent = cpu_delta / elapsed / max(1, os.cpu_count() or 1) * 100.0
    return {
        "cpu_percent": round(max(0.0, cpu_percent), 1),
        "ram_mb": round(max(0.0, ram_mb), 1),
    }


def exact_process(pid: int, executable: Path, required_command_parts: tuple[str, ...]) -> bool:
    actual_exe = executable_path(pid)
    cmd = command_line(pid)
    if not actual_exe or not cmd:
        return False
    try:
        expected = str(Path(executable).resolve()).lower().replace("/", "\\")
        actual = str(Path(actual_exe).resolve()).lower().replace("/", "\\")
    except Exception:
        return False
    if actual != expected:
        return False
    normalized = cmd.lower().replace('"', "").replace("/", "\\")
    return all(
        str(part).lower().replace('"', "").replace("/", "\\") in normalized
        for part in required_command_parts
    )

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


def exact_php_server(
    pid: int,
    port: int,
    public_dir: Path,
    executable: Path | None = None,
) -> bool:
    if executable is not None:
        actual_exe = executable_path(pid)
        if not actual_exe:
            return False
        try:
            if Path(actual_exe).resolve() != Path(executable).resolve():
                return False
        except Exception:
            return False
    cmd = command_line(pid)
    if not cmd:
        return False
    normalized = cmd.lower().replace('"', "")
    bind = f"-s 127.0.0.1:{int(port)}"
    root = f"-t {str(public_dir)}".lower()
    return bind in normalized and root in normalized

def http_alive(url: str, timeout: float = 2.0, path: str = "/fr/login") -> bool:
    probe_path = path if path.startswith("/") else "/" + path
    req = urllib.request.Request(
        url.rstrip("/") + probe_path,
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


def stop_exact(
    pid: int,
    port: int,
    public_dir: Path,
    timeout: float = 8.0,
    executable: Path | None = None,
) -> None:
    if not exact_php_server(pid, port, public_dir, executable):
        raise RuntimeError(
            f"STOP: refusing to terminate non-exact PHP server pid={pid}"
        )
    if os.name == "nt":
        proc = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            creationflags=WINDOWS_NO_WINDOW,
        )
        if proc.returncode not in {0, 128}:
            raise RuntimeError(
                f"taskkill_failed:pid={pid}:{proc.stdout[:500]}"
            )
    else:
        os.kill(pid, 15)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        clear_process_cache()
        if not pid_alive(pid):
            return
        time.sleep(0.1)
    raise RuntimeError(f"stop_timeout:pid={pid}")

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
