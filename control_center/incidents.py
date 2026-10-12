from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

_LEVELS = {"INFO", "WARNING", "ERROR", "CRITICAL"}


class IncidentStore:
    def __init__(self, runtime_root: Path):
        self.root = Path(runtime_root) / "incidents"
        self.path = self.root / "incidents.json"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _id(code: str, source: str) -> str:
        return hashlib.sha256(f"{code}|{source}".encode("utf-8")).hexdigest()[:20]

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def sync(self, issues: list[dict]) -> list[dict]:
        data = self._load()
        rows = data.get("incidents")
        rows = rows if isinstance(rows, list) else []
        by_id = {str(r.get("id")): dict(r) for r in rows if isinstance(r, dict) and r.get("id")}
        now = self._now()
        active_ids: set[str] = set()
        changed = False

        for raw in issues:
            code = str(raw.get("code") or "unknown")
            source = str(raw.get("source") or "system")
            incident_id = self._id(code, source)
            active_ids.add(incident_id)
            severity = str(raw.get("severity") or "ERROR").upper()
            if severity not in _LEVELS:
                severity = "ERROR"
            message = str(raw.get("message") or code)[:1000]
            log_key = raw.get("log_key")
            current = by_id.get(incident_id)
            if current and current.get("active") and current.get("severity") == severity and current.get("message") == message and current.get("log_key") == log_key:
                continue
            by_id[incident_id] = {
                "id": incident_id,
                "code": code,
                "source": source,
                "severity": severity,
                "message": message,
                "log_key": log_key,
                "active": True,
                "first_seen_at": current.get("first_seen_at") if current else now,
                "last_seen_at": now,
                "acknowledged_at": current.get("acknowledged_at") if current else None,
                "resolved_at": None,
            }
            changed = True

        for incident_id, row in by_id.items():
            if incident_id not in active_ids and row.get("active"):
                row["active"] = False
                row["resolved_at"] = now
                row["last_seen_at"] = now
                changed = True

        payload = {
            "schema": "ezs.incidents.v1",
            "updated_at": now,
            "incidents": sorted(by_id.values(), key=lambda r: str(r.get("last_seen_at") or ""), reverse=True)[:200],
        }
        if changed or not self.path.exists():
            self._save(payload)
        return [dict(r) for r in payload["incidents"] if r.get("active")]

    def acknowledge(self, incident_id: str) -> dict:
        incident_id = str(incident_id or "").strip()
        if not incident_id:
            raise ValueError("incident_id_required")
        data = self._load()
        rows = data.get("incidents")
        rows = rows if isinstance(rows, list) else []
        now = self._now()
        for row in rows:
            if isinstance(row, dict) and str(row.get("id")) == incident_id:
                row["acknowledged_at"] = now
                data["updated_at"] = now
                self._save(data)
                return dict(row)
        raise KeyError("incident_not_found")

    def snapshot(self, include_resolved: bool = False) -> list[dict]:
        rows = self._load().get("incidents")
        rows = rows if isinstance(rows, list) else []
        if include_resolved:
            return [dict(r) for r in rows if isinstance(r, dict)]
        return [dict(r) for r in rows if isinstance(r, dict) and r.get("active")]
