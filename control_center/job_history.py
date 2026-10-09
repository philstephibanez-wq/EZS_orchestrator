from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path

class JobHistory:
    _RC = re.compile(r"\breturncode=(-?\d+)\b")
    _KIND = re.compile(r'"kind"\s*:\s*"([^"]+)"')
    _EVENT = re.compile(r'"event"\s*:\s*"([^"]+)"')
    _SONG_ID = re.compile(r'"song_id"\s*:\s*(\d+)')
    _SONG_TITLE = re.compile(r'"song_title"\s*:\s*"([^"]*)"')

    def __init__(self, orchestrator_root: Path):
        self.root = Path(orchestrator_root).resolve()
        self.jobs_root = self.root / "runtime" / "jobs"

    @staticmethod
    def _read_json(path: Path):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _tail(path: Path, max_bytes: int = 16384):
        if not path.is_file():
            return ""
        try:
            size = path.stat().st_size
            with path.open("rb") as handle:
                handle.seek(max(0, size - max_bytes))
                return handle.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _record(self, target: str, job_dir: Path, run_dir: Path):
        rp, lp = run_dir/"result.json", run_dir/"execution.log"
        result, tail = self._read_json(rp), self._tail(lp)

        raw_job_id = result.get("job_id")
        if raw_job_id is None and job_dir.name != "_unknown":
            raw_job_id = job_dir.name
        job_id = str(raw_job_id) if raw_job_id is not None else "-"

        kind = result.get("kind")
        if not kind:
            m = self._KIND.search(tail)
            kind = m.group(1) if m else "-"

        song_id = result.get("song_id")
        if song_id is None:
            m = self._SONG_ID.search(tail)
            song_id = int(m.group(1)) if m else None

        song_title = result.get("song_title") or result.get("title")
        if not song_title:
            m = self._SONG_TITLE.search(tail)
            song_title = m.group(1) if m else None

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
            elif event in ("job_error", "job_failed"):
                state = "failed"
            elif result:
                state = "completed"
            else:
                state = "running"
        if state in ("success", "succeeded", "done", "complete"):
            state = "completed"
        if state in ("error", "failure"):
            state = "failed"

        error = result.get("error") or result.get("message") or result.get("failure")
        if state not in ("failed", "finalize_error"):
            error = None

        timestamp = (
            result.get("ended_at") or result.get("finished_at")
            or result.get("completed_at") or result.get("updated_at")
            or result.get("at") or result.get("timestamp")
        )
        if not timestamp:
            p = rp if rp.exists() else lp
            try:
                timestamp = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
            except Exception:
                timestamp = ""

        return {
            "job_id": job_id,
            "target": target,
            "song_id": song_id,
            "song_title": str(song_title) if song_title else None,
            "kind": str(kind or "-"),
            "state": state,
            "timestamp": str(timestamp or ""),
            "analysis_returncode": result.get("analysis_returncode", rc),
            "finalize_status": result.get("finalize_status"),
            "returncode": rc,
            "error": str(error)[:240] if error else None,
            "run": run_dir.name,
        }

    def recent(self, limit: int = 40):
        rows = []
        if not self.jobs_root.is_dir():
            return rows
        for target in ("dev", "prod", "lab"):
            tr = self.jobs_root/target
            if not tr.is_dir():
                continue
            for jd in tr.iterdir():
                if not jd.is_dir():
                    continue
                for rd in jd.iterdir():
                    if not rd.is_dir():
                        continue
                    files = [p for p in (rd/"result.json", rd/"execution.log") if p.exists()]
                    if not files:
                        continue
                    try:
                        mt = max(p.stat().st_mtime for p in files)
                    except Exception:
                        mt = 0
                    rows.append((mt, target, jd, rd))
        rows.sort(key=lambda x: x[0], reverse=True)
        return [self._record(t,j,r) for _,t,j,r in rows[:max(1,limit)]]

    def payload(self, limit: int = 40):
        jobs = self.recent(limit)
        return {"ok": True, "count": len(jobs), "jobs": jobs}
