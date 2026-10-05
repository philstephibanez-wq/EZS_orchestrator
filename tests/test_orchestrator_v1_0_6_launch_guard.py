from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")

required = [
    "function Get-Port8700Owner",
    "function Test-EzsControlCenterProcess",
    "function Stop-ExistingControlCenter",
    "Get-CimInstance Win32_Process",
    'control_center\\.web',
    "processus étranger",
    "Stop-Process -Id $pid8700 -Force",
    "Start-Process powershell.exe",
    "service.service_cli status",
    "service.service_cli start --target all",
    "Start-Process $ControlCenterUrl",
]

for needle in required:
    assert needle in src, needle

assert 'Stop-Process -Id $pid8700 -Force' in src
assert 'throw "Port 8700 déjà occupé par un processus étranger' in src

print("EZS_ORCHESTRATOR_V1_0_6_LAUNCH_GUARD_OK")
