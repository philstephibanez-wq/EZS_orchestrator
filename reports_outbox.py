"""Explicit, non-periodic draining of LAB completed PROFILE events.

Only a caller-provided orchestration action executes this. No watcher or timer.
"""
from __future__ import annotations
import os
from pathlib import Path
import sqlite3
from reports_review_event import publish_completed_revision, _legacy_active

DB = Path("H:/EZStudio_lab/data/benchmark.sqlite")

def drain(*, limit: int = 10) -> dict:
    if os.environ.get("EZS_EVENT_REPORTS_ENABLED") != "1":
        return {"ok":False,"state":"disabled","published":0}
    if _legacy_active():
        return {"ok":False,"state":"legacy_tasks_active","published":0}
    if not DB.is_file():
        return {"ok":False,"state":"lab_db_missing","published":0}
    if limit < 1 or limit > 100:
        raise ValueError("limit_out_of_range")
    connection=sqlite3.connect(str(DB),timeout=5)
    try:
        connection.execute("PRAGMA busy_timeout=5000")
        rows=connection.execute(
            "SELECT revision_id, run_id FROM profile_report_events "
            "WHERE state='pending' ORDER BY revision_id LIMIT ?",(limit,)).fetchall()
        success=0
        failed=0
        for revision_id, run_id in rows:
            # The publish function verifies the run's completed state again,
            # and prevents bulk/backlog publication.
            try:
                result=publish_completed_revision(int(revision_id))
                if result.get("status") != "published":
                    failed+=1
                    continue
                update=connection.execute(
                    "UPDATE profile_report_events SET state='published',"
                    "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') "
                    "WHERE revision_id=? AND run_id=? AND state='pending'",
                    (revision_id,run_id))
                connection.commit()
                success+=int(update.rowcount==1)
            except (OSError,RuntimeError,ValueError,sqlite3.Error):
                failed+=1
        return {"ok":failed==0,"state":"processed","published":success,"failed":failed,"pending_seen":len(rows)}
    except sqlite3.OperationalError as exc:
        return {"ok":False,"state":"outbox_not_ready","error":type(exc).__name__,"published":0}
    finally:
        connection.close()
