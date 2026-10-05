from __future__ import annotations

import sys
import threading

import json
from datetime import datetime, timezone
from pathlib import Path

from contracts.target import Target
from runtime_support.atomic_json import atomic_write_json


SCHEMA = "ezs.analysis-capability.v1"


class AnalysisCapabilityPublisher:
    """Publish a target-owned capability snapshot for EZScore.

    The Orchestrator is the only writer. Each EZScore checkout reads only the
    file under its own var/runtime tree, so DEV never reads PROD state and PROD
    never reads DEV state.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._write_lock = threading.Lock()

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
        try:
            with self._write_lock:
                atomic_write_json(path, payload)
        except OSError as exc:
            print(
                "CAPABILITY_PUBLISH_WARNING "
                f"target={target.value} path={path} "
                f"error={type(exc).__name__}:{exc}",
                file=sys.stderr,
                flush=True,
            )
        return payload
