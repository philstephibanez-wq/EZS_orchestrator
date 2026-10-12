from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from runtime_support.atomic_json import atomic_write_json


class LabCircuitBreaker:
    def __init__(self, runtime_root: Path, *, threshold: int = 3, cooldown_seconds: float = 60.0):
        self.path = Path(runtime_root) / "service" / "lab-circuit.json"
        self.threshold = max(1, int(threshold))
        self.cooldown_seconds = max(10.0, float(cooldown_seconds))

    @staticmethod
    def _stamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def snapshot(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def can_attempt(self) -> tuple[bool, dict]:
        state = self.snapshot()
        now = time.time()
        open_until = float(state.get("open_until_epoch") or 0.0)
        if open_until > now:
            return False, state
        if open_until:
            state = {
                "schema": "ezs.lab-circuit.v1",
                "state": "closed",
                "failures": 0,
                "threshold": self.threshold,
                "open_until_epoch": 0,
                "updated_at": self._stamp(),
            }
            atomic_write_json(self.path, state)
        return True, state

    def record_success(self) -> None:
        self.path.unlink(missing_ok=True)

    def record_failure(self, error: str) -> dict:
        allowed, state = self.can_attempt()
        if not allowed:
            return state
        failures = int(state.get("failures") or 0) + 1
        opened = failures >= self.threshold
        now = time.time()
        payload = {
            "schema": "ezs.lab-circuit.v1",
            "state": "open" if opened else "closed",
            "failures": failures,
            "threshold": self.threshold,
            "last_error": str(error)[:500],
            "open_until_epoch": now + self.cooldown_seconds if opened else 0,
            "updated_at": self._stamp(),
        }
        atomic_write_json(self.path, payload)
        return payload

    def reset(self) -> None:
        self.path.unlink(missing_ok=True)
