"""Publish a sanitized, read-only Orchestrator jobs snapshot to the private reports repo.

No job actions, no database writes, no credentials in the report.
Requires the already-authenticated gh CLI; designed for scheduled invocation.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import json
import re
import subprocess
import urllib.request

DEST = "philstephibanez-wq/EZStudio_Run_Reports"
STATES = {"waiting", "queued", "running", "completed", "failed", "cancelled", "error"}
KINDS = {"profile", "assistant.profile.review"}

def snapshot(endpoint="http://127.0.0.1:8700/api/jobs"):
    req = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("orchestrator_jobs_invalid")
    jobs = []
    for row in payload["jobs"]:
        if not isinstance(row, dict) or row.get("target") != "lab" or row.get("kind") not in KINDS:
            continue
        try:
            job_id, run_id = int(row["job_id"]), int(row["run_id"])
        except (KeyError, TypeError, ValueError):
            continue
        if job_id <= 0 or run_id <= 0:
            continue
        status = str(row.get("state") or "").lower()
        jobs.append({"job_id": job_id, "run_id": run_id,
                     "kind": row["kind"], "state": status if status in STATES else "unknown",
                     "source": str(row.get("source") or "")[:40]})
    return {"schema": "ezstudio.orchestrator-jobs.v1",
            "producer": "orchestrator", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "/api/jobs", "job_count": len(jobs), "jobs": jobs,
            "queue_errors": sorted(k for k in (payload.get("queue_errors") or {}) if re.fullmatch("[a-z_]{1,40}", str(k))),
            "note": "Read-only snapshot; not a scientific or documentary validation"}

def gh(endpoint, *, payload=None):
    cmd = ["gh", "api"]
    if payload is not None:
        cmd += ["--method", "PUT"]
    cmd.append(endpoint)
    if payload is not None:
        cmd += ["--input", "-"]
    result = subprocess.run(cmd, input=json.dumps(payload).encode("utf-8") if payload else None,
                            capture_output=True, timeout=40, check=False)
    if result.returncode:
        raise RuntimeError("github_publish_failed_exit_" + str(result.returncode))
    return json.loads(result.stdout)

def publish(report):
    # One bounded rolling state file to avoid excessive Git repository growth.
    path = "diagnostics/orchestrator/jobs/latest.json"
    endpoint = f"repos/{DEST}/contents/{path}"
    raw = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(raw) > 100000:
        raise ValueError("orchestrator_report_too_large")
    try:
        old = gh(endpoint)
    except RuntimeError:
        old = None
    encoded = base64.b64encode(raw).decode("ascii")
    update = {"message": "report(orchestrator): sanitized canonical job visibility snapshot",
              "branch": "main", "content": encoded}
    if old:
        update["sha"] = old["sha"]
    gh(endpoint, payload=update)
    verified = gh(endpoint)
    if base64.b64decode(verified.get("content", "")) != raw:
        raise RuntimeError("orchestrator_report_roundtrip_mismatch")
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = snapshot()
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("ORCHESTRATOR_REPORT=" + publish(report))

if __name__ == "__main__":
    main()
