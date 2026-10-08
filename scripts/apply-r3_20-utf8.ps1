$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZS_orchestrator UTF8 R3.20 APPLY ==="

& $Python .\scripts\migrate-r3_20-utf8.py
if($LASTEXITCODE-ne 0){throw "R3.20 source migration failed"}

& $Python -m py_compile `
  .\control_center\cli.py `
  .\service\runner.py `
  .\executor\runner.py
if($LASTEXITCODE-ne 0){throw "R3.20 Python compile failed"}

& $Python .\tests\test_r3_20_utf8_contract.py
if($LASTEXITCODE-ne 0){throw "R3.20 contract failed"}

Write-Host "EZS_ORCHESTRATOR_UTF8_R3_20_APPLY_OK"
