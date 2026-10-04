from __future__ import annotations

from pathlib import Path
from .singleton import ExecutionSingleton, ExecutionSingletonBusy


def analysis_execution_active(runtime_root: Path) -> bool:
    probe = ExecutionSingleton(Path(runtime_root))
    try:
        probe.acquire(target="lifecycle-probe")
    except ExecutionSingletonBusy:
        return True
    else:
        probe.release()
        return False
