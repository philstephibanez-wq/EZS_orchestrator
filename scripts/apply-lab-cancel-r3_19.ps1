$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZS_orchestrator LAB CANCEL R3.19 APPLY ==="

& $Python .\scripts\migrate-lab-cancel-r3_19.py
if($LASTEXITCODE-ne 0){throw "R3.19 source migration failed"}

& $Python -m py_compile `
  .\transport\jobs.py `
  .\executor\runner.py `
  .\orchestration\service.py `
  .\service\runner.py
if($LASTEXITCODE-ne 0){throw "R3.19 Python compile failed"}

& $Python .\tests\test_r3_19_lab_cancel_contract.py
if($LASTEXITCODE-ne 0){throw "R3.19 contract failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_CANCEL_R3_19_APPLY_OK"
