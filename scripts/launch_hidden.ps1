$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Logs = Join-Path $Root "logs"
$Runtime = Join-Path $Root "runtime"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

$Python = "H:\Python\pythoncore-3.14-64\python.exe"
$ControlCenterUrl = "http://127.0.0.1:8700/"
$OutLog = Join-Path $Logs "control-center.log"
$ErrLog = Join-Path $Logs "control-center-error.log"
$SplashScript = Join-Path $Root "scripts\show_splash.ps1"
$ReadyFile = Join-Path $Runtime "control-center-launch.ready"
$FailureFile = Join-Path $Runtime "control-center-launch.failed"

Remove-Item -LiteralPath $ReadyFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $FailureFile -Force -ErrorAction SilentlyContinue

if (Test-Path -LiteralPath $SplashScript -PathType Leaf) {
    Start-Process powershell.exe `
        -WindowStyle Hidden `
        -ArgumentList @(
            "-NoProfile",
            "-STA",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$SplashScript`"",
            "-ReadyFile", "`"$ReadyFile`"",
            "-FailureFile", "`"$FailureFile`""
        ) | Out-Null
}

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

function Preserve-CurrentControlCenterToken {
    $tokenPath = Join-Path $Runtime "control-center-ui.token"

    if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
        return
    }

    $pid8700 = Get-Port8700Owner
    if ($null -eq $pid8700) {
        return
    }

    if (-not (Test-EzsControlCenterProcess -ProcessId $pid8700)) {
        return
    }

    try {
        $page = Invoke-WebRequest `
            -Uri $ControlCenterUrl `
            -UseBasicParsing `
            -TimeoutSec 3
    }
    catch {
        throw "Migration du token Control Center impossible : page locale inaccessible. Aucun arrêt effectué."
    }

    $match = [regex]::Match(
        [string]$page.Content,
        'const TOKEN="([A-Za-z0-9_-]{32,})";'
    )
    if (-not $match.Success) {
        throw "Migration du token Control Center impossible : token local absent ou invalide. Aucun arrêt effectué."
    }

    $token = [string]$match.Groups[1].Value
    $tmp = "$tokenPath.tmp"

    try {
        [System.IO.File]::WriteAllText(
            $tmp,
            $token + [Environment]::NewLine,
            [System.Text.Encoding]::ASCII
        )
        Move-Item -LiteralPath $tmp -Destination $tokenPath -Force
    }
    catch {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        throw "Migration du token Control Center impossible : persistance refusée. Aucun arrêt effectué."
    }
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

    throw "Ancien Orchestrator EZS arrêté mais le port 8700 reste occupé."
}

try {
    # Purge visible operational logs at every Orchestrator restart.
    # Use a real module entrypoint: Windows PowerShell 5 can mangle
    # multiline Python code passed through -c.
    $logPurgeOutput = & $Python -m control_center.log_tools clear 2>&1
    $logPurgeExitCode = $LASTEXITCODE
    if ($logPurgeExitCode -ne 0) {
        throw "Impossible de purger les logs au redémarrage. $($logPurgeOutput -join ' | ')"
    }

    # 1. Ensure the permanent service is running on the currently installed code.
    #    If an analysis is active, service_cli leaves the current service untouched.
    $serviceReloadOutput = & $Python -m service.service_cli restart-if-idle --target all --poll-seconds 2 2>&1
    $serviceReloadExitCode = $LASTEXITCODE
    $serviceReloadOutput | Set-Content -LiteralPath (Join-Path $Logs "service-start.log") -Encoding utf8
    if ($serviceReloadExitCode -ne 0) {
        throw "Impossible de charger le service permanent EZS."
    }

    # 1b. Reconcile each Caddy proxy after reboot using the canonical manager.
    # Never stop/restart an existing owned instance. Failures are logged per
    # target, so a LAB failure cannot prevent DEV/PROD reconciliation.
    $caddyResults = @()
    $caddyFailures = @()
    foreach ($target in @("dev", "prod", "lab")) {
        $caddyOutput = & $Python -m caddy_manager.cli start --target $target 2>&1
        $caddyCode = $LASTEXITCODE
        $caddyText = ($caddyOutput | Out-String).Trim()
        $caddyResults += ("[{0}] exit={1} {2}" -f $target, $caddyCode, $caddyText)
        if ($caddyCode -ne 0 -or $caddyText -notmatch "http=True") {
            $caddyFailures += $target
        }
    }
    $caddyResults | Set-Content -LiteralPath (Join-Path $Logs "caddy-start.log") -Encoding utf8
    if ($caddyFailures.Count -gt 0) {
        Add-Content -LiteralPath $ErrLog -Value ("CADDY_START_FAILURE targets=" + ($caddyFailures -join ",")) -Encoding utf8
    }
    if ($caddyFailures -contains "dev") {
        throw "CADDY_DEV_NOT_READY: consulter logs\\caddy-start.log"
    }

    # 2. launch.bat means: run the currently installed Orchestrator.
    #    Restart our own listener, but never kill an unrelated process on 8700.
    Preserve-CurrentControlCenterToken
    Stop-ExistingControlCenter
    # 3. Start Orchestrator directly. Do not keep a PowerShell wrapper
    #    alive for the lifetime of the Python HTTP server.
    Start-Process $Python `
        -WindowStyle Hidden `
        -WorkingDirectory $Root `
        -ArgumentList @(
            "-m", "control_center.web",
            "--port", "8700", "--no-browser"
        ) `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog | Out-Null

    # 4. Wait for the actual listener.
    for ($i = 0; $i -lt 50; $i++) {
        Start-Sleep -Milliseconds 200
        if (Test-Port8700) { break }
    }

    if (-not (Test-Port8700)) {
        throw "L'Orchestrator EZS n'a pas ouvert le port 8700."
    }

    # 5. Verify that the newly listening process is ours.
    $newPid = Get-Port8700Owner
    if (-not (Test-EzsControlCenterProcess -ProcessId $newPid)) {
        throw "Le port 8700 s'est ouvert, mais le listener n'est pas l'Orchestrator EZS attendu (PID=$newPid)."
    }

    Set-Content -LiteralPath $ReadyFile -Value ([DateTime]::UtcNow.ToString("o")) -Encoding ascii
    Start-Process $ControlCenterUrl
}
catch {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $message = "[$stamp] $($_.Exception.Message)"

    # Failure marker first: the splash must never wait forever because
    # an error log is temporarily locked by another process.
    Set-Content -LiteralPath $FailureFile -Value $message -Encoding utf8
    try {
        Add-Content -Path $ErrLog -Value $message -ErrorAction Stop
    }
    catch {
        # The failure marker above is authoritative for the splash.
    }
    exit 1
}
