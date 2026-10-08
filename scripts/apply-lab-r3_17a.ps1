$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17A APPLY ==="

python .\scripts\migrate-lab-r3_17a.py
if ($LASTEXITCODE -ne 0) { throw "LAB migration failed" }

python -m py_compile `
  .\contracts\target.py `
  .\config\loader.py `
  .\transport\targets.py `
  .\executor\planner.py `
  .\capability\publisher.py `
  .\service\runner.py `
  .\service\service_cli.py `
  .\control_center\cli.py `
  .\control_center\job_history.py `
  .\tests\test_r3_17a_lab_target.py `
  .\tests\test_r3_17a_non_regression_static.py

if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }

python -m unittest `
  tests.test_r3_17a_lab_target `
  tests.test_r3_17a_non_regression_static `
  tests.test_r3_2_explicit_target `
  tests.test_r3_4_target_python `
  tests.test_r3_4a_runtime_boundary `
  tests.test_r3_5_execution_singleton `
  tests.test_r3_6_service `
  tests.test_r3_9_visual_control_center `
  tests.test_r3_11_analysis_capability

if ($LASTEXITCODE -ne 0) { throw "Focused regression suite failed" }

python .\tests\test_orchestrator_v1_0_contract.py
if ($LASTEXITCODE -ne 0) { throw "Orchestrator V1.0 contract failed" }

Write-Host "EZS_ORCHESTRATOR_LAB_R3_17A_APPLY_OK"
