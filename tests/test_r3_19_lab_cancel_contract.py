
from pathlib import Path
root = Path(__file__).resolve().parents[1]
checks = {
    "transport/jobs.py": ["def cancel_requested(", "def cancelled(", "/cancelled"],
    "executor/runner.py": [
        "cancelled: bool = False",
        "def _terminate_process_tree(",
        "should_cancel: Callable[[], bool]",
        '["taskkill", "/PID", str(proc.pid), "/T", "/F"]',
    ],
    "orchestration/service.py": [
        '"event": "job_cancelled"',
        "self.transport.cancelled(",
        "should_cancel=lambda:",
    ],
    "service/runner.py": [
        'parsed.get("event") == "job_cancelled"',
        'state = "cancelled"',
    ],
}
for rel, needles in checks.items():
    src = (root / rel).read_text(encoding="utf-8")
    for needle in needles:
        assert needle in src, f"{rel}: {needle}"
print("EZS_ORCHESTRATOR_LAB_CANCEL_R3_19_CONTRACT_OK")
