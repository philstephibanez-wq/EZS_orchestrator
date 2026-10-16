$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python orchestrator introuvable: $Python"
}

function Get-Port8700Owner {
    $listener = Get-NetTCPConnection `
        -LocalAddress "127.0.0.1" `
        -LocalPort 8700 `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $listener) { return $null }
    return [int]$listener.OwningProcess
}

function Test-EzsControlCenterProcess([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
    }
    catch {
        return $false
    }
    if ($null -eq $proc) { return $false }

    $exe = [string]$proc.ExecutablePath
    $cmd = [string]$proc.CommandLine
    if ([string]::IsNullOrWhiteSpace($exe) -or [string]::IsNullOrWhiteSpace($cmd)) {
        return $false
    }

    $expectedPython = [System.IO.Path]::GetFullPath($Python).ToLowerInvariant()
    $actualExe = [System.IO.Path]::GetFullPath($exe).ToLowerInvariant()

    return (
        $actualExe -eq $expectedPython -and
        $cmd -match '(?i)(^|\s)-m\s+control_center\.web(\s|$)'
    )
}

Write-Host "[EZS] Arrêt du Control Center..."

$pid8700 = Get-Port8700Owner
if ($null -ne $pid8700) {
    if (-not (Test-EzsControlCenterProcess -ProcessId $pid8700)) {
        $proc = Get-Process -Id $pid8700 -ErrorAction SilentlyContinue
        $name = if ($null -ne $proc) { $proc.ProcessName } else { "inconnu" }
        throw "Port 8700 occupé par un processus étranger (PID=$pid8700, process=$name). Aucun kill."
    }

    Stop-Process -Id $pid8700 -Force -ErrorAction Stop

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 100
        if ($null -eq (Get-Port8700Owner)) { break }
    }

    if ($null -ne (Get-Port8700Owner)) {
        throw "Control Center arrêté mais port 8700 toujours occupé."
    }
}

Write-Host "[EZS] Arrêt du worker permanent..."
Push-Location $Root
try {
    & $Python -m service.service_cli stop --wait-seconds 20
    $serviceRc = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($serviceRc -ne 0) {
    throw "Arrêt du worker permanent non confirmé (rc=$serviceRc)."
}

Write-Host "EZS_ORCHESTRATOR_STOP_OK"
