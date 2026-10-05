# EZS Orchestrator V1.0.6.1 — PowerShell PID fix

Correction ciblée de V1.0.6.

PowerShell possède une variable automatique `$PID`, insensible à la casse et en lecture seule.
Le paramètre `-Pid` de `Test-EzsControlCenterProcess` entrait donc en collision avec `$PID`.

Correction :
- `Pid` -> `ProcessId`
- aucun autre comportement du Launch Guard n'est modifié.

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_6_1_LAUNCH_PID_FIX.zip" `
  -C H:\EZS_orchestrator
```

## Validation

```powershell
H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_6_1_launch_pid_fix.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_6_launch_guard.py
```

Puis refaire le test réel BEFORE/AFTER avec `.\launch.bat`.
