from __future__ import annotations

import importlib.util
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_log_tools() -> None:
    module = load_module("r314_log_tools", ROOT / "control_center" / "log_tools.py")
    LogTools = module.LogTools

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "logs" / "servers").mkdir(parents=True)
        (root / "runtime" / "service").mkdir(parents=True)
        (root / "var" / "storage").mkdir(parents=True)

        log1 = root / "logs" / "servers" / "dev.err.log"
        log2 = root / "runtime" / "service" / "service.out.log"
        metadata = root / "runtime" / "service" / "service.json"
        secret = root / ".env.local"
        db = root / "data.sqlite"
        storage = root / "var" / "storage" / "private.txt"

        log1.write_text("dev-error\n", encoding="utf-8")
        log2.write_text("service\n", encoding="utf-8")
        metadata.write_text('{"pid": 123}\n', encoding="utf-8")
        secret.write_text("SECRET=do-not-export\n", encoding="utf-8")
        db.write_bytes(b"sqlite")
        storage.write_text("private-user-data\n", encoding="utf-8")

        tools = LogTools(root)
        archive = tools.export_zip()

        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            assert "manifest.json" in names
            assert "logs/servers/dev.err.log" in names
            assert "runtime/service/service.out.log" in names
            assert "runtime/service/service.json" in names
            assert ".env.local" not in names
            assert "data.sqlite" not in names
            assert "var/storage/private.txt" not in names

        result = tools.clear_logs()
        assert result.cleared == 2
        assert result.failed == ()

        # R3.14 physically truncated logs. R3.14.1 intentionally switched to
        # a logical clear (watermark) so active Windows log files stay intact.
        # The base contract accepts both generations; R3.14.1 behavior is
        # validated more strictly in test_r3141_safe_logs.py.
        if hasattr(tools, "tail"):
            assert log1.read_text(encoding="utf-8") == "dev-error\n"
            assert log2.read_text(encoding="utf-8") == "service\n"
            assert tools.tail(log1) == []
            assert tools.tail(log2) == []
        else:
            assert log1.read_bytes() == b""
            assert log2.read_bytes() == b""

        assert metadata.read_text(encoding="utf-8") == '{"pid": 123}\n'
        assert secret.read_text(encoding="utf-8") == "SECRET=do-not-export\n"


def test_source_contracts() -> None:
    web = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
    process = (ROOT / "server_manager" / "process.py").read_text(encoding="utf-8")
    service = (ROOT / "service" / "service_cli.py").read_text(encoding="utf-8")
    launch = (ROOT / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8")

    assert 'id="clearLogs"' in web
    assert 'id="exportLogs"' in web
    assert 'path == "/api/logs/export"' in web
    assert "refreshInFlight" in web
    assert "devFailures<3" in web
    assert "prodFailures<3" in web
    assert "SNAPSHOT_CACHE_SECONDS = 1.0" in web
    assert "timeout: float = 2.0" in process
    assert "_CACHE_TTL_SECONDS = 1.0" in process
    assert "ctypes.windll.kernel32.OpenProcess" in process
    assert "_live_metadata_pid" in service
    assert "_cleanup_stale" in service
    assert "no forced termination performed" in service
    assert "start --target all --poll-seconds 2" in launch


if __name__ == "__main__":
    test_log_tools()
    test_source_contracts()
    print("R3_14_CONTRACT_OK")
