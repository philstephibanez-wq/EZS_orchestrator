$ErrorActionPreference = "Stop"
Set-Location "H:\EZS_orchestrator"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $Python)) { throw "Python orchestrator introuvable: $Python" }

Write-Host "=== R3.10 COMPILE ==="
& $Python -m compileall -q .\gateway_manager .\prod_lifecycle .\caddy_manager .\control_center .\tests\test_r3_10_prod_lifecycle.py
if ($LASTEXITCODE -ne 0) { throw "Compile R3.10 en echec." }

Write-Host "=== R3.10 PROD LIFECYCLE CONTRACT ==="
& $Python -m unittest .\tests\test_r3_10_prod_lifecycle.py -v
if ($LASTEXITCODE -ne 0) { throw "Contrat R3.10 en echec." }

Write-Host "=== R3.9 NON-REGRESSION ==="
& $Python -m unittest .\tests\test_r3_9_visual_control_center.py -v
if ($LASTEXITCODE -ne 0) { throw "Regression R3.9 detectee." }

Write-Host "=== FULL TEST SUITE ==="
& $Python -m unittest discover -s .\tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Suite complete en echec." }

Write-Output "EZS_ORCHESTRATOR_R3_10_PROD_LIFECYCLE_OK"
