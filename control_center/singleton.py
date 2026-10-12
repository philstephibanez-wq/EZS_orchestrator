from __future__ import annotations

import json
import os
import socket
import sys
import time
import uuid
from pathlib import Path


class ControlCenterSingletonBusy(RuntimeError):
    pass


class ControlCenterSingleton:
    WINDOWS_MUTEX_NAME = r"Global\EZS_orchestrator_control_center_v1"
    ERROR_ALREADY_EXISTS = 183

    def __init__(self, runtime_root: Path):
        self.root = Path(runtime_root) / "control_center"
        self.meta_path = self.root / "instance.json"
        self.instance_id = str(uuid.uuid4())
        self._handle = None
        self._fd = None
        self._held = False

    def _write_meta(self, port: int) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "ezs.control-center.instance.v1",
            "pid": os.getpid(),
            "instance_id": self.instance_id,
            "hostname": socket.gethostname(),
            "python": sys.executable,
            "port": int(port),
            "started_at": time.time(),
        }
        tmp = self.meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.meta_path)

    def acquire(self, port: int) -> None:
        if self._held:
            return
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
            kernel32.CreateMutexW.restype = wintypes.HANDLE
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            ctypes.set_last_error(0)
            handle = kernel32.CreateMutexW(None, True, self.WINDOWS_MUTEX_NAME)
            if not handle:
                raise OSError(ctypes.get_last_error(), "CreateMutexW failed")
            if ctypes.get_last_error() == self.ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(handle)
                raise ControlCenterSingletonBusy("EZS Orchestrator Control Center already active")
            self._handle = handle
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            lock = self.root / "control-center.lock"
            try:
                self._fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                raise ControlCenterSingletonBusy("EZS Orchestrator Control Center already active") from exc
            os.write(self._fd, str(os.getpid()).encode("ascii"))
        self._held = True
        try:
            self._write_meta(port)
        except Exception:
            self.release()
            raise

    def release(self) -> None:
        if not self._held:
            return
        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
                kernel32.ReleaseMutex.restype = wintypes.BOOL
                kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                kernel32.CloseHandle.restype = wintypes.BOOL
                if self._handle:
                    kernel32.ReleaseMutex(self._handle)
                    kernel32.CloseHandle(self._handle)
                    self._handle = None
            else:
                lock = self.root / "control-center.lock"
                if self._fd is not None:
                    os.close(self._fd)
                    self._fd = None
                lock.unlink(missing_ok=True)
        finally:
            self._held = False
            self.meta_path.unlink(missing_ok=True)
