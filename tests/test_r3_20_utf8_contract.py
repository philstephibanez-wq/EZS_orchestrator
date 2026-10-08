from pathlib import Path

root=Path(__file__).resolve().parents[1]
cli=(root/'control_center'/'cli.py').read_text(encoding='utf-8')
service=(root/'service'/'runner.py').read_text(encoding='utf-8')
executor=(root/'executor'/'runner.py').read_text(encoding='utf-8')

for needle in [
    'R3_20_UTF8_CONSOLE',
    '_configure_utf8_console()',
    'encoding="utf-8"',
    'errors="backslashreplace"',
]:
    assert needle in cli, needle

assert 'encoding="utf-8"' in executor
assert 'errors="replace"' in executor
assert '_safe_stream_write' in service
assert 'encoding="utf-8"' in service

print('EZS_ORCHESTRATOR_UTF8_R3_20_CONTRACT_OK')
