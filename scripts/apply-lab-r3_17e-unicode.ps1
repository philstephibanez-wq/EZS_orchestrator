$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17E UNICODE HOTFIX APPLY ==="

python .\scripts\migrate-lab-r3_17e-unicode.py
if($LASTEXITCODE-ne 0){throw "R3.17E migration failed"}

python -m py_compile `
  .\service\runner.py `
  .\tests\test_r3_17e_unicode_output.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

python -m unittest `
  tests.test_r3_17e_unicode_output `
  tests.test_r3_17a_lab_target `
  tests.test_r3_17b_hotfix_contract `
  tests.test_r3_17d_tests_hotfix_contract `
  tests.test_r3_5_execution_singleton `
  tests.test_r3_6_service
if($LASTEXITCODE-ne 0){throw "R3.17E focused regression failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_R3_17E_FOCUSED_REGRESSION_OK"
Write-Host "EZS_ORCHESTRATOR_LAB_R3_17E_APPLY_OK"
