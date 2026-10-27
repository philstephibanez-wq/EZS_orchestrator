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
    if not WATCHER.is_file():
        return {"status": "error", "reason": "lab_watcher_missing"}
    if not (LAB / "data/benchmark.sqlite").is_file():
        return {"status": "error", "reason": "lab_db_missing"}
    # Refuse concurrent legacy publishers; maintain one writer for published.json.
    if os.name == "nt":
        query = ("$t = @(Get-ScheduledTask -ErrorAction Stop | "
                 "Where-Object { $_.TaskName -in @('EZStudio_Run_Reports_Publisher','EZStudio_Run_Reports_Watcher') -and "
                 "$_.State -ne 'Disabled' }); "
                 "if ($t.Count -gt 0) { exit 42 }")
        result = subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-WindowStyle","Hidden",
                                 "-Command",query],capture_output=True,text=True,timeout=15,
                                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if result.returncode != 0:
            return {"status": "skipped", "reason": "legacy_tasks_active_or_unverified"}
    STATE.mkdir(parents=True,exist_ok=True)
    process = subprocess.run([sys.executable, "-u", str(WATCHER), "--once", "--state-dir",str(STATE)],
                             cwd=str(LAB),capture_output=True,text=True,timeout=180,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    return {"status": "published" if process.returncode == 0 else "error",
            "exit_code": process.returncode}
