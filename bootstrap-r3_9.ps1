$ErrorActionPreference = "Stop"
Set-Location "H:\EZS_orchestrator"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
Write-Host "=== R3.9 COMPILE ==="
& $Python -m compileall -q .\control_center
if ($LASTEXITCODE -ne 0) { throw "Compile R3.9 en echec." }
Write-Host "=== R3.9 CONTROL CENTER CONTRACT ==="
& $Python -m unittest .\tests\test_r3_9_visual_control_center.py -v
if ($LASTEXITCODE -ne 0) { throw "Contrat R3.9 en echec." }
Write-Host "=== SAFE IMPORT ==="
& $Python -c "from control_center.web import HOST,DEFAULT_PORT; print('HOST=',HOST,'PORT=',DEFAULT_PORT)"
if ($LASTEXITCODE -ne 0) { throw "Import R3.9 en echec." }
Write-Output "EZS_ORCHESTRATOR_R3_9_CONTROL_CENTER_OK"
