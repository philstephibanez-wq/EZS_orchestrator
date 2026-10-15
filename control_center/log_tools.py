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
    """Safe Orchestrator log diagnostics with physical log clearing."""

    MAX_TAIL_BYTES = 256 * 1024

    def __init__(self, orchestrator_root: Path) -> None:
        self.root = Path(orchestrator_root).resolve()
        self.export_dir = self.root / "runtime" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

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

        logs_root = self.root / "logs"
        if logs_root.exists():
            for path in logs_root.rglob("*.log"):
                if self._is_allowed_log(path):
                    files.add(path)

        runtime = self.root / "runtime"
        excluded_runtime_dirs = {"jobs", "exports"}
        if runtime.exists():
            for path in runtime.glob("*.log"):
                if self._is_allowed_log(path):
                    files.add(path)
            for child in runtime.iterdir():
                if not child.is_dir():
                    continue
                if child.name.lower() in excluded_runtime_dirs:
                    continue
                for path in child.rglob("*.log"):
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

    def clear_logs(self) -> LogClearResult:
        """Physically truncate every log managed by the Log Center."""
        failed: list[str] = []
        cleared = 0

        for path in self.log_files():
            rel = self._relative_key(path)
            try:
                with path.open("r+b") as handle:
                    handle.truncate(0)
                    handle.flush()
                cleared += 1
            except Exception as exc:
                failed.append(f"{rel}: {exc}")

        legacy_state = self.root / "runtime" / "logs" / "clear_state.json"
        try:
            legacy_state.unlink(missing_ok=True)
        except Exception as exc:
            failed.append(f"runtime/logs/clear_state.json: {exc}")

        return LogClearResult(cleared=cleared, failed=tuple(failed))

    def read_visible_bytes(self, path: Path) -> bytes:
        if not self._is_allowed_log(path):
            return b""
        try:
            return path.read_bytes()
        except Exception:
            return b""

    def tail(self, path: Path, max_lines: int = 80) -> list[str]:
        if not self._is_allowed_log(path):
            return []
        try:
            size = int(path.stat().st_size)
            if size <= 0:
                return []
            start = max(0, size - self.MAX_TAIL_BYTES)
            with path.open("rb") as handle:
                handle.seek(start)
                raw = handle.read(size - start)
            if start > 0:
                first_newline = raw.find(b"\n")
                raw = raw[first_newline + 1:] if first_newline >= 0 else b""
            return raw.decode("utf-8", errors="replace").splitlines()[-max_lines:]
        except Exception as exc:
            return [f"[log read error] {exc}"]

    def error_alerts(self, max_lines_per_file: int = 80) -> list[dict]:
        """Return actionable errors from the current physical log contents."""
        rels = (
            "logs/control-center-error.log",
            "runtime/service/service.err.log",
            "logs/servers/dev.err.log",
            "logs/servers/prod.err.log",
            "logs/servers/lab.err.log",
            "logs/gateway/prod.err.log",
            "runtime/caddy/dev/caddy.err.log",
            "runtime/caddy/prod/caddy.err.log",
            "runtime/caddy/lab/caddy.err.log",
        )
        benign = (
            "connectionabortederror",
            "winerror 10053",
            "context canceled",
        )
        indicators = (
            "[error]",
            "traceback (most recent call last)",
            "exception",
            "fatal",
            "failed",
            "permissionerror",
            "syntaxerror",
            "accessdeniedhttpexception",
            "invalid analysis worker token",
        )
        alerts: list[dict] = []
        for rel in rels:
            path = self.root / rel
            lines = self.tail(path, max_lines=max_lines_per_file)
            lowered_lines = [line.lower() for line in lines]
            for index, line in enumerate(lines):
                lowered = lowered_lines[index]
                if any(term in lowered for term in benign):
                    continue
                if not any(term in lowered for term in indicators):
                    continue
                if rel == "logs/control-center-error.log":
                    start = index
                    while (
                        start > 0
                        and not lines[start - 1].startswith(
                            "----------------------------------------"
                        )
                    ):
                        start -= 1
                    end = index
                    while (
                        end + 1 < len(lines)
                        and not lines[end + 1].startswith(
                            "----------------------------------------"
                        )
                    ):
                        end += 1
                    block = "\n".join(lowered_lines[start:end + 1])
                    if any(term in block for term in benign):
                        continue
                elif (
                    "traceback (most recent call last)" in lowered
                    or "exception occurred during processing of request" in lowered
                ):
                    context = "\n".join(lowered_lines[index:index + 32])
                    if any(term in context for term in benign):
                        continue
                alerts.append({"source": rel, "line": line[:500]})
        return alerts[-20:]

    def export_zip(self) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        target = self.export_dir / f"EZS_orchestrator_logs_{stamp}.zip"
        manifest = {
            "schema": "ezs.orchestrator.log-export.v2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "orchestrator_root": str(self.root),
            "clear_mode": "physical-truncate",
            "policy": {
                "included": [
                    "Current Orchestrator log files after any physical clear",
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

def main() -> int:
    import sys

    from config.loader import load_runtime_config

    if len(sys.argv) != 2 or sys.argv[1] != "clear":
        print("usage: python -m control_center.log_tools clear")
        return 2

    result = LogTools(load_runtime_config().orchestrator_root).clear_logs()
    print(f"LOGS_PURGED cleared={result.cleared} failed={len(result.failed)}")
    for item in result.failed:
        print(item)
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
