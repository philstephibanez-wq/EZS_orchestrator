$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZS_orchestrator LAB VISIBILITY R3.18 APPLY ==="

& $Python .\scripts\migrate-lab-visibility-r3_18.py
if($LASTEXITCODE-ne 0){throw "LAB visibility migration failed"}

& $Python -m py_compile .\control_center\web.py
if($LASTEXITCODE-ne 0){throw "control_center/web.py compile failed"}

& $Python .\tests\test_r3_18_lab_visibility.py
if($LASTEXITCODE-ne 0){throw "R3.18 contract failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_VISIBILITY_R3_18_APPLY_OK"
