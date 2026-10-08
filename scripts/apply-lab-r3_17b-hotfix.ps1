$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17B HOTFIX APPLY ==="

python .\scripts\migrate-lab-r3_17b-hotfix.py
if($LASTEXITCODE-ne 0){throw "R3.17B migration failed"}

python -m py_compile `
  .\executor\planner.py `
  .\tests\test_r3_2_explicit_target.py `
  .\tests\test_r3_17b_hotfix_contract.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

python -m unittest `
  tests.test_r3_17b_hotfix_contract `
  tests.test_r3_17a_lab_target `
  tests.test_r3_17a_non_regression_static `
  tests.test_r3_2_explicit_target `
  tests.test_r3_4_target_python `
  tests.test_r3_4a_runtime_boundary `
  tests.test_r3_5_execution_singleton `
  tests.test_r3_6_service `
  tests.test_r3_9_visual_control_center `
  tests.test_r3_11_analysis_capability
if($LASTEXITCODE-ne 0){throw "Focused regression suite failed"}

python .\tests\test_orchestrator_v1_0_contract.py
if($LASTEXITCODE-ne 0){throw "Orchestrator V1.0 contract failed"}

Write-Host "EZS_ORCHESTRATOR_LAB_R3_17B_FOCUSED_REGRESSION_OK"
Write-Host "EZS_ORCHESTRATOR_LAB_R3_17B_HOTFIX_APPLY_OK"
