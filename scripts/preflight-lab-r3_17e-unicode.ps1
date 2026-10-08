$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17E FULL PREFLIGHT ==="

python -m unittest discover -s tests -p "test_*.py"
if($LASTEXITCODE-ne 0){throw "Full orchestrator test suite failed"}

python .\tests\test_orchestrator_v1_0_contract.py
if($LASTEXITCODE-ne 0){throw "Orchestrator V1.0 contract failed"}

Write-Host "EZS_ORCHESTRATOR_FULL_REGRESSION_OK"
Write-Host "EZS_ORCHESTRATOR_LAB_R3_17E_PREFLIGHT_OK"
