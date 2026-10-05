from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from contracts.target import Target


SCHEMA = "ezs.analysis-capability.v1"


class AnalysisCapabilityPublisher:
    """Publish a target-owned capability snapshot for EZScore.

    The Orchestrator is the only writer. Each EZScore checkout reads only the
    file under its own var/runtime tree, so DEV never reads PROD state and PROD
    never reads DEV state.
    """

    def __init__(self, config) -> None:
        self.config = config

    def _root_for(self, target: Target) -> Path:
        return self.config.dev.root if target is Target.DEV else self.config.prod.root

    def path_for(self, target: Target) -> Path:
        return (
            self._root_for(target)
            / "var"
            / "runtime"
            / "orchestrator"
            / "analysis-capability.json"
        )

    def publish(
        self,
        target: Target,
        *,
        available: bool,
        state: str,
        service_scope: str,
        queued: int | None = None,
        active_target: str | None = None,
        error: str | None = None,
    ) -> dict:
        payload = {
            "schema": SCHEMA,
            "target": target.value,
            "available": bool(available),
            "state": str(state),
            "service_scope": service_scope,
            "queued": queued,
            "active_target": active_target,
            "error": error,
            "at": datetime.now(timezone.utc).isoformat(),
        }

        path = self.path_for(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)
        return payload
