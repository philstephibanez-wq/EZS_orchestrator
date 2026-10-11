param(
    [ValidateSet("plan","deploy")][string]$Command = "plan",
    [string]$Node = "steph@192.168.1.81"
)
$ErrorActionPreference = "Stop"
Set-Location "H:\EZS_orchestrator"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python orchestrator introuvable: $Python"
}
& $Python -m assistant_deployment.manager $Command --node $Node
exit $LASTEXITCODE
