$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZS_orchestrator LAB VISIBILITY R3.18 PREFLIGHT ==="

& $Python .\tests\test_r3_18_lab_visibility.py
if($LASTEXITCODE-ne 0){throw "R3.18 contract failed"}

& $Python -m unittest discover -s tests -p "test_r3_17*.py"
if($LASTEXITCODE-ne 0){throw "R3.17 regression tests failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_VISIBILITY_R3_18_PREFLIGHT_OK"
