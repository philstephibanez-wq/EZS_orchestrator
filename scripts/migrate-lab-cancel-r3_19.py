
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def patch(path: Path, old: str, new: str, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"ALREADY {path}: {marker}")
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: anchor count={count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"PATCHED {path}")

p = ROOT / "transport" / "jobs.py"
patch(
    p,
    '''    def progress(self, target: Target, job_id: int, percent: int) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/progress",
            {"progress": int(percent)},
        )

''',
    '''    def status(self, target: Target, job_id: int) -> dict:
        data = self.registry.endpoint(target).client().get(
            f"/internal/analysis/desktop/jobs/{job_id}/context"
        )
        return data if isinstance(data, dict) else {}

    def cancel_requested(self, target: Target, job_id: int) -> bool:
        status = str(self.status(target, job_id).get("status") or "").lower()
        return status in {"cancelling", "cancelled"}

    def progress(self, target: Target, job_id: int, percent: int) -> None:
        self.registry.endpoint(target).client().post(
            f"/internal/analysis/desktop/jobs/{job_id}/progress",
            {"progress": int(percent)},
        )

''',
    "def cancel_requested(",
)
patch(
    p,
    '''    def fail(self, target: Target, job_id: int, error: str) -> None:
        try:
            self.registry.endpoint(target).client().post(
                f"/internal/analysis/desktop/jobs/{job_id}/fail",
                {"error": str(error)[:400]},
            )
        finally:
            self._execution_singleton.release()

''',
    '''    def cancelled(self, target: Target, job_id: int) -> None:
        try:
            self.registry.endpoint(target).client().post(
                f"/internal/analysis/desktop/jobs/{job_id}/cancelled", {}
            )
        finally:
            self._execution_singleton.release()

    def fail(self, target: Target, job_id: int, error: str) -> None:
        try:
            self.registry.endpoint(target).client().post(
                f"/internal/analysis/desktop/jobs/{job_id}/fail",
                {"error": str(error)[:400]},
            )
        finally:
            self._execution_singleton.release()

''',
    "def cancelled(",
)

p = ROOT / "executor" / "runner.py"
patch(
    p,
    '''@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout_tail: tuple[str, ...]
''',
    '''@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout_tail: tuple[str, ...]
    cancelled: bool = False
''',
    "cancelled: bool = False",
)
patch(
    p,
    '''    @staticmethod
    def _validate_runtime_files(plan: ExecutionPlan) -> None:
''',
    '''    @staticmethod
    def _terminate_process_tree(proc: subprocess.Popen) -> None:
        if proc.poll() is not None:
            return
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=WINDOWS_NO_WINDOW,
            )
            if completed.returncode == 0:
                return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    @staticmethod
    def _validate_runtime_files(plan: ExecutionPlan) -> None:
''',
    "def _terminate_process_tree(",
)
patch(
    p,
    '''        on_output: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        timeout: float | None = None,
''',
    '''        on_output: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
        timeout: float | None = None,
''',
    "should_cancel: Callable[[], bool]",
)
patch(
    p,
    '''            stop_progress = threading.Event()
            progress_thread: threading.Thread | None = None

            if on_progress is not None and progress_path is not None:
''',
    '''            stop_progress = threading.Event()
            progress_thread: threading.Thread | None = None
            stop_cancel = threading.Event()
            cancel_thread: threading.Thread | None = None
            cancellation_seen = threading.Event()

            if should_cancel is not None:
                def watch_cancel() -> None:
                    while not stop_cancel.wait(0.25):
                        try:
                            if should_cancel():
                                cancellation_seen.set()
                                if on_output is not None:
                                    on_output(f"cancellation_requested:job_id={job.job_id}")
                                self._terminate_process_tree(proc)
                                return
                        except Exception as exc:
                            if on_output is not None:
                                on_output(
                                    "cancellation_callback_error:"
                                    f"{type(exc).__name__}:{exc}"
                                )

                cancel_thread = threading.Thread(
                    target=watch_cancel,
                    name=f"ezs-cancel-{job.job_id}",
                    daemon=True,
                )
                cancel_thread.start()

            if on_progress is not None and progress_path is not None:
''',
    "cancellation_seen = threading.Event()",
)
patch(
    p,
    '''            except Exception:
                if proc.poll() is None:
                    proc.terminate()
                raise
            finally:
                stop_progress.set()
                if progress_thread is not None:
                    progress_thread.join(timeout=1.0)

            return ExecutionResult(returncode, tuple(tail))
''',
    '''            except Exception:
                if proc.poll() is None:
                    self._terminate_process_tree(proc)
                raise
            finally:
                stop_progress.set()
                stop_cancel.set()
                if progress_thread is not None:
                    progress_thread.join(timeout=1.0)
                if cancel_thread is not None:
                    cancel_thread.join(timeout=1.0)

            return ExecutionResult(
                returncode,
                tuple(tail),
                cancelled=cancellation_seen.is_set(),
            )
''',
    "cancelled=cancellation_seen.is_set()",
)

p = ROOT / "orchestration" / "service.py"
patch(
    p,
    '''            result: ExecutionResult = self.executor.run(
                claimed,
                on_output=on_output,
                on_progress=publish_progress,
            )

            if result.returncode == 0:
''',
    '''            result: ExecutionResult = self.executor.run(
                claimed,
                on_output=on_output,
                on_progress=publish_progress,
                should_cancel=lambda: self.transport.cancel_requested(
                    target, claimed.job_id
                ),
            )

            if result.cancelled:
                self.transport.cancelled(target, claimed.job_id)
                if on_output is not None:
                    on_output(json.dumps({
                        "event": "job_cancelled",
                        "job_id": claimed.job_id,
                        "kind": claimed.kind,
                    }, ensure_ascii=False))
                return RunOutcome(
                    target=target,
                    job_id=claimed.job_id,
                    returncode=0,
                )

            if result.returncode == 0:
''',
    '"event": "job_cancelled"',
)

p = ROOT / "service" / "runner.py"
patch(
    p,
    '''        operator_meta = {}
        finalize_meta = {}
        for line in combined.splitlines():
''',
    '''        operator_meta = {}
        finalize_meta = {}
        cancelled_meta = {}
        for line in combined.splitlines():
''',
    "cancelled_meta = {}",
)
patch(
    p,
    '''            if parsed.get("event") == "job_meta":
                operator_meta = parsed
            elif parsed.get("event") == "job_finalize_error":
                finalize_meta = parsed
''',
    '''            if parsed.get("event") == "job_meta":
                operator_meta = parsed
            elif parsed.get("event") == "job_finalize_error":
                finalize_meta = parsed
            elif parsed.get("event") == "job_cancelled":
                cancelled_meta = parsed
''',
    'parsed.get("event") == "job_cancelled"',
)
patch(
    p,
    '''        if finalize_meta:
            state = "finalize_error"
            analysis_returncode = 0
            finalize_status = "error"
            error = str(finalize_meta.get("error") or "complete_callback_failed")[:500]
        elif returncode == 0:
''',
    '''        if cancelled_meta:
            state = "cancelled"
            analysis_returncode = 0
            finalize_status = "cancelled"
            error = None
        elif finalize_meta:
            state = "finalize_error"
            analysis_returncode = 0
            finalize_status = "error"
            error = str(finalize_meta.get("error") or "complete_callback_failed")[:500]
        elif returncode == 0:
''',
    'state = "cancelled"',
)

print("EZS_ORCHESTRATOR_LAB_CANCEL_R3_19_SOURCE_OK")
