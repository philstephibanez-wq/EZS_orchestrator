$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

New-Item -ItemType Directory -Force -Path `
    (Join-Path $Root "runtime"), `
    (Join-Path $Root "logs") | Out-Null

$Config = Join-Path $Root "config\runtime.json"
if (-not (Test-Path $Config)) {
    throw "Config absente: $Config"
}

$Python = "H:\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "H:\EZScore\.venv-py313\Scripts\python.exe"
}
if (-not (Test-Path $Python)) {
    throw "Python introuvable."
}

& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests R1 en échec."
}

& $Python -m control_center.cli status
if ($LASTEXITCODE -ne 0) {
    throw "Smoke Control Center en échec."
}

Write-Output "EZS_ORCHESTRATOR_R1_BOOTSTRAP_OK"
