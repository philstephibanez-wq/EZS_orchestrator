from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path

class JobHistory:
    _RC = re.compile(r"\breturncode=(-?\d+)\b")
    _KIND = re.compile(r'"kind"\s*:\s*"([^"]+)"')
    _EVENT = re.compile(r'"event"\s*:\s*"([^"]+)"')

    def __init__(self, orchestrator_root: Path):
        self.root = Path(orchestrator_root).resolve()
        self.jobs_root = self.root / "runtime" / "jobs"

    def _read_json(self, p: Path):
        try:
            v = json.loads(p.read_text(encoding="utf-8"))
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}

    def _tail(self, p: Path, n=16384):
        try:
            size = p.stat().st_size
            with p.open("rb") as f:
                f.seek(max(0, size-n))
                return f.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _record(self, target: str, job_dir: Path, run_dir: Path):
        rp, lp = run_dir/"result.json", run_dir/"execution.log"
        result, tail = self._read_json(rp), self._tail(lp)
        job_id = str(result.get("job_id", job_dir.name))
        kind = result.get("kind")
        if not kind:
            m = self._KIND.search(tail); kind = m.group(1) if m else "-"
        rc = result.get("returncode", result.get("return_code"))
        if rc is None:
            ms = self._RC.findall(tail)
            rc = int(ms[-1]) if ms else None
        event = (self._EVENT.findall(tail) or [""])[-1]
        state = str(result.get("state") or result.get("status") or "").lower()
        if not state:
            if rc is not None:
                state = "completed" if int(rc) == 0 else "failed"
            elif event == "job_complete":
                state = "completed"
            elif event in ("job_error","job_failed"):
                state = "failed"
            else:
                state = "running"
        if state in ("success","succeeded","done","complete"):
            state = "completed"
        if state in ("error","failure"):
            state = "failed"
        err = result.get("error") or result.get("message")
        if state != "failed":
            err = None
        ts = result.get("finished_at") or result.get("completed_at") or result.get("updated_at") or result.get("at")
        if not ts:
            p = rp if rp.exists() else lp
            try:
                ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
            except Exception:
                ts = ""
        return {
            "job_id": job_id, "target": target, "kind": str(kind or "-"),
            "state": state, "timestamp": str(ts or ""), "returncode": rc,
            "error": str(err)[:240] if err else None, "run": run_dir.name
        }

    def recent(self, limit=40):
        rows = []
        if not self.jobs_root.is_dir():
            return rows
        for target in ("dev","prod"):
            tr = self.jobs_root/target
            if not tr.is_dir():
                continue
            for jd in tr.iterdir():
                if not jd.is_dir(): continue
                for rd in jd.iterdir():
                    if not rd.is_dir(): continue
                    files = [p for p in (rd/"result.json", rd/"execution.log") if p.exists()]
                    if not files: continue
                    try: mt = max(p.stat().st_mtime for p in files)
                    except Exception: mt = 0
                    rows.append((mt,target,jd,rd))
        rows.sort(key=lambda x:x[0], reverse=True)
        return [self._record(t,j,r) for _,t,j,r in rows[:max(1,limit)]]

    def payload(self, limit=40):
        jobs = self.recent(limit)
        return {"ok": True, "count": len(jobs), "jobs": jobs}
