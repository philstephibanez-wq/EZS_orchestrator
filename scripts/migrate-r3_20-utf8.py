from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'control_center'/'cli.py'
text=path.read_text(encoding='utf-8')

if 'R3_20_UTF8_CONSOLE' in text:
    print('R3.20 CLI UTF-8 already patched')
else:
    if 'import sys\n' not in text:
        text=text.replace('import json\n','import json\nimport sys\n',1)

    anchor='def parse_target(value: str) -> Target:\n'
    helper=(
        'R3_20_UTF8_CONSOLE = True\n\n'
        'def _configure_utf8_console() -> None:\n'
        '    for stream in (sys.stdout, sys.stderr):\n'
        '        reconfigure = getattr(stream, "reconfigure", None)\n'
        '        if callable(reconfigure):\n'
        '            try:\n'
        '                reconfigure(\n'
        '                    encoding="utf-8",\n'
        '                    errors="backslashreplace",\n'
        '                )\n'
        '            except Exception:\n'
        '                pass\n\n\n'
    )
    if anchor not in text:
        raise RuntimeError('control_center.cli parse_target anchor missing')
    text=text.replace(anchor,helper+anchor,1)

    main_anchor='def main() -> int:\n'
    if main_anchor not in text:
        raise RuntimeError('control_center.cli main anchor missing')
    text=text.replace(main_anchor,main_anchor+'    _configure_utf8_console()\n',1)

    path.write_text(text,encoding='utf-8')
    print('R3.20 control_center CLI UTF-8 patched')

print('EZS_ORCHESTRATOR_UTF8_R3_20_SOURCE_OK')
