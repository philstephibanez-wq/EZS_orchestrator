from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any


def atomic_write_json(
    path: Path,
    payload: dict[str, Any],
    *,
    retries: int = 8,
    initial_delay: float = 0.02,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    )
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    try:
        tmp.write_text(data, encoding="utf-8")
        delay = max(0.0, float(initial_delay))
        attempts = max(1, int(retries))

        for index in range(attempts):
            try:
                os.replace(tmp, path)
                return
            except (PermissionError, OSError):
                if index >= attempts - 1:
                    raise
                if delay > 0:
                    time.sleep(delay)
                    delay = min(max(delay * 2.0, 0.01), 0.25)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
