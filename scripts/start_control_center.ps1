param([int]$Port = 8700)
$ErrorActionPreference = "Stop"
Set-Location "H:\EZS_orchestrator"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $Python)) { throw "Python orchestrator introuvable: $Python" }
Write-Host "[EZS] Control Center: http://127.0.0.1:$Port/"
& $Python -m control_center.web --port $Port --no-browser
