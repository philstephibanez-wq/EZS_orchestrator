$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "H:\EZS_orchestrator"

$Python = "H:\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "H:\EZScore\.venv-py313\Scripts\python.exe"
}
if (-not (Test-Path $Python)) {
    throw "Python introuvable."
}

& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests R2.1 en échec."
}

& $Python -m control_center.cli status
if ($LASTEXITCODE -ne 0) {
    throw "Smoke R2.1 en échec."
}

Write-Output "EZS_ORCHESTRATOR_R2_1_CONTRACT_OK"
