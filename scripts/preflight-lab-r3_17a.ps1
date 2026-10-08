$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== EZS_orchestrator LAB R3.17A PREFLIGHT ==="

python -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) { throw "Full orchestrator test suite failed" }

python -m control_center.cli queue --target dev
if ($LASTEXITCODE -ne 0) { throw "DEV queue regression" }

python -m control_center.cli queue --target prod
if ($LASTEXITCODE -ne 0) { throw "PROD queue regression" }

# LAB may legitimately be unavailable until EZStudio_lab exposes the endpoint/token.
# Its failure is reported but does not invalidate DEV/PROD non-regression.
python -m control_center.cli queue --target lab
$labRc = $LASTEXITCODE
if ($labRc -eq 0) {
    Write-Host "EZS_ORCHESTRATOR_LAB_TRANSPORT_READY"
} else {
    Write-Host "EZS_ORCHESTRATOR_LAB_TRANSPORT_PENDING rc=$labRc"
}

Write-Host "EZS_ORCHESTRATOR_DEV_PROD_NON_REGRESSION_OK"
Write-Host "EZS_ORCHESTRATOR_LAB_R3_17A_PREFLIGHT_OK"
