$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m service.service_cli status
python -m control_center.cli queue --target dev
python -m control_center.cli queue --target prod
python -m control_center.cli queue --target lab
