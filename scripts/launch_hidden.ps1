$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$Python = "H:\Python\pythoncore-3.14-64\python.exe"
$ControlCenterUrl = "http://127.0.0.1:8700/"
$OutLog = Join-Path $Logs "control-center.log"
$ErrLog = Join-Path $Logs "control-center-error.log"
$StartScript = Join-Path $Root "scripts\start_control_center.ps1"

function Get-Port8700Owner {
    $listener = Get-NetTCPConnection `
        -LocalAddress "127.0.0.1" `
        -LocalPort 8700 `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($null -eq $listener) {
        return $null
    }

    return [int]$listener.OwningProcess
}

function Test-Port8700 {
    return ($null -ne (Get-Port8700Owner))
}

function Test-EzsControlCenterProcess([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
    }
    catch {
        return $false
    }

    if ($null -eq $proc) {
        return $false
    }

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

function Stop-ExistingControlCenter {
    $pid8700 = Get-Port8700Owner
    if ($null -eq $pid8700) {
        return
    }

    if (-not (Test-EzsControlCenterProcess -ProcessId $pid8700)) {
        $proc = Get-Process -Id $pid8700 -ErrorAction SilentlyContinue
        $name = if ($null -ne $proc) { $proc.ProcessName } else { "inconnu" }

        throw "Port 8700 déjà occupé par un processus étranger (PID=$pid8700, process=$name). Arrêt de sécurité : EZS Orchestrator ne tue pas ce processus."
    }

    Stop-Process -Id $pid8700 -Force -ErrorAction Stop

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 100
        if (-not (Test-Port8700)) {
            return
        }
    }

    throw "Ancien Control Center EZS arrêté mais le port 8700 reste occupé."
}

# 1. Ensure the permanent service is running.
$serviceStatus = & $Python -m service.service_cli status 2>&1
if ($LASTEXITCODE -ne 0 -or ($serviceStatus -join "`n") -notmatch "SERVICE:\s+running") {
    & $Python -m service.service_cli start --target all --poll-seconds 2 *> (Join-Path $Logs "service-start.log")
    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de démarrer le service permanent EZS."
    }
}

# 2. launch.bat means: run the currently installed Control Center.
#    Restart our own listener, but never kill an unrelated process on 8700.
Stop-ExistingControlCenter

# 3. Start the current Control Center implementation.
if (-not (Test-Path $StartScript)) {
    throw "Script de démarrage Control Center introuvable: $StartScript"
}

Start-Process powershell.exe `
    -WindowStyle Hidden `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$StartScript`""
    ) `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog | Out-Null

# 4. Wait for the actual listener.
for ($i = 0; $i -lt 50; $i++) {
    Start-Sleep -Milliseconds 200
    if (Test-Port8700) { break }
}

if (-not (Test-Port8700)) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $ErrLog -Value "[$stamp] Control Center did not open port 8700."
    throw "Le Control Center EZS n'a pas ouvert le port 8700."
}

# 5. Verify that the newly listening process is ours.
$newPid = Get-Port8700Owner
if (-not (Test-EzsControlCenterProcess -ProcessId $newPid)) {
    throw "Le port 8700 s'est ouvert, mais le listener n'est pas le Control Center EZS attendu (PID=$newPid)."
}

Start-Process $ControlCenterUrl
