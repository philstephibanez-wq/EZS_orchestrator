"""Event-driven run report publication, invoked after confirmed LAB completion.

No scheduled tasks; no polling; existing LAB publisher handles deduplication.
Disabled by default until Windows legacy tasks are explicitly retired.
"""
import os
from pathlib import Path
import subprocess
import sys

LAB = Path("H:/EZStudio_lab")
WATCHER = LAB / "scripts/watch_run_reports.py"
STATE = Path("H:/EZStudio_Run_Reports_state")

def notify_completed(*, job_id: int, kind: str, target: str) -> dict:
    if target != "lab" or kind == "assistant.profile.review":
        # Dispatch is not proof of a terminal expertise; LAB's later completion
        # must be the authoritative event. Never publish premature drafts.
        return {"status": "skipped", "reason": "not_final_lab_analysis"}
    if os.environ.get("EZS_EVENT_REPORTS_ENABLED") != "1":
        return {"status": "skipped", "reason": "not_enabled"}
    # A completion event must NEVER run the bulk --once watcher: it scans old
    # LAB and Assistant reports. Enable only after a per-run publisher exists.
    return {"status": "skipped", "reason": "targeted_lab_run_publisher_required"}
