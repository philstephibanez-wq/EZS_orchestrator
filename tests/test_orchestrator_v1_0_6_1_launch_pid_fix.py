from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root / "scripts" / "launch_hidden.ps1").read_text(encoding="utf-8-sig")

assert "function Test-EzsControlCenterProcess([int]$ProcessId)" in src
assert "-ProcessId $pid8700" in src
assert "-ProcessId $newPid" in src
assert "([int]$Pid)" not in src
assert "-Pid $pid8700" not in src
assert "-Pid $newPid" not in src

for needle in (
    "function Get-Port8700Owner",
    "function Stop-ExistingControlCenter",
    "Get-CimInstance Win32_Process",
    "control_center\\.web",
    "processus étranger",
    "Stop-Process -Id $pid8700 -Force",
    "Start-Process powershell.exe",
):
    assert needle in src, needle

print("EZS_ORCHESTRATOR_V1_0_6_1_LAUNCH_PID_FIX_OK")
