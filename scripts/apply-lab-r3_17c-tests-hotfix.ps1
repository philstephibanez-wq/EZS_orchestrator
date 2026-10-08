$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17C TESTS HOTFIX APPLY ==="

python .\scripts\migrate-lab-r3_17c-tests-hotfix.py
if($LASTEXITCODE-ne 0){throw "R3.17C migration failed"}

python -m py_compile `
  .\tests\test_orchestrator_v1_0_4_header.py `
  .\tests\test_orchestrator_v1_0_7_3_deploy_modal.py `
  .\tests\test_r3_3_claim_failure_cleanup.py `
  .\tests\test_r3_12_dev_php_x64.py `
  .\tests\test_r3_17c_tests_hotfix_contract.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

python -m unittest `
  tests.test_r3_17c_tests_hotfix_contract `
  tests.test_orchestrator_v1_0_4_header `
  tests.test_orchestrator_v1_0_7_3_deploy_modal `
  tests.test_r3_3_claim_failure_cleanup `
  tests.test_r3_12_dev_php_x64
if($LASTEXITCODE-ne 0){throw "R3.17C targeted tests failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_R3_17C_TARGETED_TESTS_OK"
Write-Host "EZS_ORCHESTRATOR_LAB_R3_17C_APPLY_OK"
