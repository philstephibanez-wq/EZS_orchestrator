from __future__ import annotations

import json
import os
import socket
import sys
import time
import uuid
from pathlib import Path


class ServiceSingletonBusy(RuntimeError):
    pass


class ServiceSingleton:
    WINDOWS_MUTEX_NAME = r"Global\EZS_orchestrator_service_v1"
    ERROR_ALREADY_EXISTS = 183

    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.lock_dir = self.runtime_root / "service"
        self.meta_path = self.lock_dir / "service.json"
        self.instance_id = str(uuid.uuid4())
        self._handle = None
        self._fd = None
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    def _write_meta(self, *, target: str, poll_seconds: float) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "ezs.orchestrator.service.v1",
            "pid": os.getpid(),
            "instance_id": self.instance_id,
            "hostname": socket.gethostname(),
            "started_at": time.time(),
            "target": target,
            "poll_seconds": poll_seconds,
        }
        tmp = self.meta_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.meta_path)

    def _acquire_windows(self) -> None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, True, self.WINDOWS_MUTEX_NAME)
        if not handle:
            raise OSError(ctypes.get_last_error(), "CreateMutexW failed")

        if ctypes.get_last_error() == self.ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            raise ServiceSingletonBusy(
                "EZS_orchestrator permanent service already active"
            )
        self._handle = handle

    def _release_windows(self) -> None:
        import ctypes
        from ctypes import wintypes

        if not self._handle:
            return

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel32.ReleaseMutex.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.ReleaseMutex(self._handle)
        kernel32.CloseHandle(self._handle)
        self._handle = None

    def _acquire_fallback(self) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        path = self.lock_dir / "service.fallback.lock"
        try:
            self._fd = os.open(
                str(path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError as exc:
            raise ServiceSingletonBusy(
                "EZS_orchestrator permanent service already active"
            ) from exc
        os.write(self._fd, str(os.getpid()).encode("ascii"))

    def _release_fallback(self) -> None:
        path = self.lock_dir / "service.fallback.lock"
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None
        path.unlink(missing_ok=True)

    def acquire(self, *, target: str, poll_seconds: float) -> None:
        if self._held:
            return
        if sys.platform == "win32":
            self._acquire_windows()
        else:
            self._acquire_fallback()
        self._held = True
        try:
            self._write_meta(target=target, poll_seconds=poll_seconds)
        except Exception:
            self.release()
            raise

    def release(self) -> None:
        if not self._held:
            return
        try:
            if sys.platform == "win32":
                self._release_windows()
            else:
                self._release_fallback()
        finally:
            self._held = False
            try:
                self.meta_path.unlink(missing_ok=True)
            except OSError:
                pass
