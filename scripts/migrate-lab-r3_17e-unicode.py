from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace_once(path:Path, old:str, new:str)->None:
    text=path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{path}: migration anchor absent")
    path.write_text(text.replace(old,new,1),encoding="utf-8",newline="\n")

def main()->int:
    runner=ROOT/"service"/"runner.py"

    replace_once(
        runner,
        "def utc_stamp() -> str:\n"
        "    return datetime.now(timezone.utc).strftime(\"%Y%m%dT%H%M%S.%fZ\")\n"
        "\n",
        "def utc_stamp() -> str:\n"
        "    return datetime.now(timezone.utc).strftime(\"%Y%m%dT%H%M%S.%fZ\")\n"
        "\n"
        "\n"
        "def _safe_stream_write(stream, value: str) -> None:\n"
        "    if not value:\n"
        "        return\n"
        "    encoding = getattr(stream, \"encoding\", None) or \"utf-8\"\n"
        "    safe = value.encode(encoding, errors=\"backslashreplace\").decode(encoding)\n"
        "    stream.write(safe)\n"
        "    stream.flush()\n"
        "\n",
    )

    replace_once(
        runner,
        "        if proc.stdout:\n"
        "            print(proc.stdout, end=\"\")\n"
        "        if proc.stderr:\n"
        "            print(proc.stderr, end=\"\", file=sys.stderr)\n",
        "        if proc.stdout:\n"
        "            _safe_stream_write(sys.stdout, proc.stdout)\n"
        "        if proc.stderr:\n"
        "            _safe_stream_write(sys.stderr, proc.stderr)\n",
    )

    print("EZS_ORCHESTRATOR_LAB_R3_17E_UNICODE_MIGRATION_OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
