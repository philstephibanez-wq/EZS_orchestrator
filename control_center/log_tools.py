from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LogClearResult:
    cleared: int
    failed: tuple[str, ...]


class LogTools:
    """Safe Orchestrator log diagnostics with logical clear watermarks."""

    MAX_TAIL_BYTES = 256 * 1024

    def __init__(self, orchestrator_root: Path) -> None:
        self.root = Path(orchestrator_root).resolve()
        self.export_dir = self.root / "runtime" / "exports"
        self.state_dir = self.root / "runtime" / "logs"
        self.clear_state_path = self.state_dir / "clear_state.json"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _inside_root(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return resolved == self.root or self.root in resolved.parents

    def _relative_key(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.root)).replace("\\", "/")

    def _is_allowed_log(self, path: Path) -> bool:
        if not path.is_file() or not self._inside_root(path):
            return False
        try:
            rel = path.resolve().relative_to(self.root)
        except ValueError:
            return False
        parts = tuple(part.lower() for part in rel.parts)
        if len(parts) >= 2 and parts[0] == "runtime" and parts[1] == "jobs":
            return False
        if len(parts) >= 2 and parts[0] == "runtime" and parts[1] == "exports":
            return False
        return path.suffix.lower() == ".log"

    def log_files(self) -> list[Path]:
        files: set[Path] = set()
        for base in (self.root / "logs", self.root / "runtime"):
            if not base.exists():
                continue
            for path in base.rglob("*.log"):
                if self._is_allowed_log(path):
                    files.add(path)
        return sorted(files, key=lambda p: str(p).lower())

    def diagnostic_metadata(self) -> list[Path]:
        rels = (
            "runtime/service/service.json",
            "runtime/service/heartbeat.json",
            "runtime/servers/dev.json",
            "runtime/servers/prod.json",
            "runtime/gateway/prod/process.json",
            "runtime/caddy/dev/process.json",
            "runtime/caddy/prod/process.json",
        )
        return [
            self.root / rel
            for rel in rels
            if (self.root / rel).is_file() and self._inside_root(self.root / rel)
        ]

    def _load_state(self) -> dict[str, dict]:
        try:
            data = json.loads(self.clear_state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        files = data.get("files", {}) if isinstance(data, dict) else {}
        return files if isinstance(files, dict) else {}

    def _write_state(self, entries: dict[str, dict]) -> None:
        payload = {
            "schema": "ezs.orchestrator.log-clear-state.v1",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "files": entries,
        }
        tmp = self.clear_state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.clear_state_path)

    @staticmethod
    def _identity(st) -> tuple[int, int]:
        return int(getattr(st, "st_dev", 0) or 0), int(getattr(st, "st_ino", 0) or 0)

    def _effective_offset(self, path: Path) -> int:
        entry = self._load_state().get(self._relative_key(path))
        if not isinstance(entry, dict):
            return 0
        try:
            st = path.stat()
            offset = max(0, int(entry.get("offset", 0)))
        except Exception:
            return 0
        if int(st.st_size) < offset:
            return 0
        stored = (int(entry.get("dev", 0) or 0), int(entry.get("ino", 0) or 0))
        current = self._identity(st)
        if stored[1] and current[1] and stored != current:
            return 0
        return offset

    def clear_logs(self) -> LogClearResult:
        entries: dict[str, dict] = {}
        failed: list[str] = []
        cleared = 0
        for path in self.log_files():
            try:
                st = path.stat()
                dev, ino = self._identity(st)
                entries[self._relative_key(path)] = {
                    "offset": int(st.st_size),
                    "dev": dev,
                    "ino": ino,
                }
                cleared += 1
            except Exception as exc:
                failed.append(f"{path.relative_to(self.root)}: {exc}")
        try:
            self._write_state(entries)
        except Exception as exc:
            failed.append(f"runtime/logs/clear_state.json: {exc}")
        return LogClearResult(cleared=cleared, failed=tuple(failed))

    def read_visible_bytes(self, path: Path) -> bytes:
        if not self._is_allowed_log(path):
            return b""
        try:
            size = int(path.stat().st_size)
            offset = min(self._effective_offset(path), size)
            with path.open("rb") as handle:
                handle.seek(offset)
                return handle.read()
        except Exception:
            return b""

    def tail(self, path: Path, max_lines: int = 80) -> list[str]:
        if not self._is_allowed_log(path):
            return []
        try:
            size = int(path.stat().st_size)
            offset = min(self._effective_offset(path), size)
            if size <= offset:
                return []
            start = max(offset, size - self.MAX_TAIL_BYTES)
            with path.open("rb") as handle:
                handle.seek(start)
                raw = handle.read(size - start)
            if start > offset:
                first_newline = raw.find(b"\n")
                raw = raw[first_newline + 1:] if first_newline >= 0 else b""
            return raw.decode("utf-8", errors="replace").splitlines()[-max_lines:]
        except Exception as exc:
            return [f"[log read error] {exc}"]

    def export_zip(self) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        target = self.export_dir / f"EZS_orchestrator_logs_{stamp}.zip"
        manifest = {
            "schema": "ezs.orchestrator.log-export.v2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "orchestrator_root": str(self.root),
            "clear_mode": "logical-watermark",
            "policy": {
                "included": [
                    "Orchestrator logs after current logical-clear watermark",
                    "selected non-sensitive runtime metadata",
                ],
                "excluded": [
                    "runtime/jobs/**",
                    ".env / .env.local",
                    "databases",
                    "business storage",
                    "user media/content",
                    "tokens/secrets",
                ],
            },
        }
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            for path in self.log_files():
                zf.writestr(self._relative_key(path), self.read_visible_bytes(path))
            for path in self.diagnostic_metadata():
                zf.write(path, arcname=self._relative_key(path))
        return target
