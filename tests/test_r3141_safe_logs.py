from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_center.log_tools import LogTools


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "logs" / "servers").mkdir(parents=True)
        (root / "runtime" / "service").mkdir(parents=True)
        (root / "runtime" / "jobs" / "dev" / "123" / "run").mkdir(parents=True)
        (root / "runtime" / "caddy" / "dev").mkdir(parents=True)
        (root / "var" / "storage").mkdir(parents=True)

        dev = root / "logs" / "servers" / "dev.err.log"
        caddy = root / "runtime" / "caddy" / "dev" / "caddy.err.log"
        service = root / "runtime" / "service" / "service.out.log"
        job = root / "runtime" / "jobs" / "dev" / "123" / "run" / "execution.log"
        meta = root / "runtime" / "service" / "service.json"
        env = root / ".env.local"
        db = root / "data.sqlite"
        private = root / "var" / "storage" / "private.txt"

        dev.write_bytes(b"OLD DEV\n")
        caddy.write_bytes(b"OLD CADDY\n")
        service.write_bytes(b"OLD SERVICE\n")
        job.write_bytes(b"PRIVATE JOB DATA\n")
        meta.write_text('{"pid":123}\n', encoding="utf-8")
        env.write_text("SECRET=NO\n", encoding="utf-8")
        db.write_bytes(b"sqlite")
        private.write_text("private\n", encoding="utf-8")

        before = {p: p.read_bytes() for p in (dev, caddy, service)}
        tools = LogTools(root)

        collected = {p.relative_to(root).as_posix() for p in tools.log_files()}
        assert "runtime/jobs/dev/123/run/execution.log" not in collected

        result = tools.clear_logs()
        assert result.failed == ()
        assert result.cleared == 3
        for p, content in before.items():
            assert p.read_bytes() == content

        assert tools.tail(dev) == []
        assert tools.tail(caddy) == []
        assert tools.tail(service) == []

        for p, line in ((dev, b"NEW DEV\n"), (caddy, b"NEW CADDY\n"), (service, b"NEW SERVICE\n")):
            with p.open("ab") as f:
                f.write(line)

        assert tools.tail(dev) == ["NEW DEV"]
        assert tools.tail(caddy) == ["NEW CADDY"]
        assert tools.tail(service) == ["NEW SERVICE"]
        assert b"\x00" not in dev.read_bytes()
        assert b"\x00" not in caddy.read_bytes()
        assert b"\x00" not in service.read_bytes()

        archive = tools.export_zip()
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            assert all(not n.startswith("runtime/jobs/") for n in names)
            assert ".env.local" not in names
            assert "data.sqlite" not in names
            assert "var/storage/private.txt" not in names
            assert zf.read("logs/servers/dev.err.log") == b"NEW DEV\n"
            assert zf.read("runtime/caddy/dev/caddy.err.log") == b"NEW CADDY\n"
            assert zf.read("runtime/service/service.out.log") == b"NEW SERVICE\n"

        caddy.write_bytes(b"ROT\n")
        assert tools.tail(caddy) == ["ROT"]

    web = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
    tools_src = (ROOT / "control_center" / "log_tools.py").read_text(encoding="utf-8")
    assert "Control Center R3.15" in web
    assert "self.log_tools.tail(" in web
    assert "cleared logically" in web
    assert "handle.truncate" not in tools_src
    assert 'parts[0] == "runtime" and parts[1] == "jobs"' in tools_src
    assert "logical-watermark" in tools_src
    print("R3_14_1_SAFE_LOGS_OK")


if __name__ == "__main__":
    main()
