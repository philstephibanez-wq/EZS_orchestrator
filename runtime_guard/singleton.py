from __future__ import annotations

import json
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


class ExecutionSingletonBusy(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LockOwner:
    pid: int
    instance_id: str
    hostname: str
    started_at: float
    target: str | None = None
    job_id: int | None = None


class ExecutionSingleton:
    """Machine-wide execution singleton.

    Windows uses a named kernel mutex. The metadata file is diagnostic only;
    the kernel mutex is authoritative and is released automatically if the
    process dies.
    """

    WINDOWS_MUTEX_NAME = r"Global\EZS_orchestrator_analysis_executor_v1"
    ERROR_ALREADY_EXISTS = 183

    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.lock_dir = self.runtime_root / "locks"
        self.meta_path = self.lock_dir / "analysis-executor.json"
        self.instance_id = str(uuid.uuid4())
        self._handle = None
        self._fd: int | None = None
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    def _owner_payload(
        self,
        *,
        target: str | None = None,
        job_id: int | None = None,
    ) -> dict:
        return {
            "schema": "ezs.execution-singleton.v1",
            "pid": os.getpid(),
            "instance_id": self.instance_id,
            "hostname": socket.gethostname(),
            "started_at": time.time(),
            "target": target,
            "job_id": job_id,
        }

    def _write_metadata(
        self,
        *,
        target: str | None = None,
        job_id: int | None = None,
    ) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.meta_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                self._owner_payload(target=target, job_id=job_id),
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.meta_path)

    def update_metadata(
        self,
        *,
        target: str | None = None,
        job_id: int | None = None,
    ) -> None:
        if not self._held:
            raise RuntimeError("execution singleton is not held")
        self._write_metadata(target=target, job_id=job_id)

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

        error = ctypes.get_last_error()
        if error == self.ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            raise ExecutionSingletonBusy(
                "analysis executor already active on this machine"
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
        # Test/non-Windows fallback. The production Windows path above is
        # authoritative on EZScore hosts.
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        path = self.lock_dir / "analysis-executor.fallback.lock"
        try:
            self._fd = os.open(
                str(path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError as exc:
            raise ExecutionSingletonBusy(
                "analysis executor already active"
            ) from exc
        os.write(self._fd, str(os.getpid()).encode("ascii"))

    def _release_fallback(self) -> None:
        path = self.lock_dir / "analysis-executor.fallback.lock"
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None
        path.unlink(missing_ok=True)

    def acquire(
        self,
        *,
        target: str | None = None,
        job_id: int | None = None,
    ) -> None:
        if self._held:
            return

        if sys.platform == "win32":
            self._acquire_windows()
        else:
            self._acquire_fallback()

        self._held = True
        try:
            self._write_metadata(target=target, job_id=job_id)
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

    def __enter__(self) -> "ExecutionSingleton":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
