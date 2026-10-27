"""Explicit event publication of ONE persisted, completed LAB expertise.

No scheduler, no backlog scan for publication, no new task, no visible shell.
This is an opt-in entry point for the finalization hook (not a dispatcher).
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

LAB = Path("H:/EZStudio_lab")
STATE = Path("H:/EZStudio_Run_Reports_state")

def _legacy_active() -> bool:
    if os.name != "nt":
        return True  # Do not assume Windows scheduled task safety elsewhere.
    command = ("$ErrorActionPreference='Stop'; "
        "$t=@(Get-ScheduledTask | Where-Object { $_.TaskName -in "
        "@('EZStudio_Run_Reports_Publisher','EZStudio_Run_Reports_Watcher') -and "
        "$_.State -ne 'Disabled' }); if ($t.Count -gt 0) { exit 42 }")
    check = subprocess.run(
        ["powershell.exe","-NoProfile","-NonInteractive","-WindowStyle","Hidden",
         "-Command",command],capture_output=True,timeout=15,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    return check.returncode != 0

def publish_completed_revision(revision_id: int, *, dry_run: bool = False) -> dict:
    if type(revision_id) is not int or revision_id < 1:
        raise ValueError("positive_revision_id_required")
    if not dry_run and os.environ.get("EZS_EVENT_REPORTS_ENABLED") != "1":
        return {"status":"skipped","reason":"not_enabled"}
    dbpath = LAB / "data/benchmark.sqlite"
    if not dbpath.is_file():
        return {"status":"error","reason":"lab_db_missing"}
    if not dry_run and _legacy_active():
        return {"status":"skipped","reason":"legacy_tasks_active_or_unverified"}
    # Read only. Never mutate the scientific database or revise a verdict.
    conn = sqlite3.connect(f"file:{dbpath.resolve().as_posix()}?mode=ro",uri=True,timeout=5)
    try:
        row = conn.execute(
            "SELECT r.id,r.run_id,r.status FROM profile_external_revisions r "
            "JOIN scientific_runs sr ON sr.id=r.run_id "
            "WHERE r.id=? AND sr.item='profile' AND sr.state='done'",(revision_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None or row[2] != "completed":
        return {"status":"skipped","reason":"review_not_completed"}
    # Only exact persisted revision selected by existing publisher, never --once
    # which may upload an entire accumulated backlog.
    if not dry_run:
        STATE.mkdir(parents=True,exist_ok=True)
    script = LAB / "scripts/publish_run_reports.py"
    if not script.is_file():
        return {"status":"error","reason":"lab_publisher_missing"}
    targeted = LAB / "scripts/publish_review_event.py"
    if not targeted.is_file():
        return {"status":"error","reason":"lab_targeted_publisher_missing"}
    args = [sys.executable,"-u",str(targeted),"--revision-id",str(revision_id),
            "--state-dir",str(STATE)]
    if dry_run:
        args.append("--dry-run")
    result = subprocess.run(args,cwd=str(LAB),capture_output=True,text=True,timeout=90,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    return {"status":"ready" if dry_run and result.returncode==0 else
                     ("published" if result.returncode==0 else "error"),
            "revision_id":revision_id,"run_id":row[1],
            "exit_code":result.returncode}
