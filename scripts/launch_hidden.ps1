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
    $purgeOut = Join-Path $Logs "log-purge.out.log"
    $purgeErr = Join-Path $Logs "log-purge.err.log"
    $purge = Start-Process -FilePath $Python -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
        -ArgumentList @("-m", "control_center.log_tools", "clear") `
        -RedirectStandardOutput $purgeOut -RedirectStandardError $purgeErr
    $logPurgeOutput = @(
        Get-Content -LiteralPath $purgeOut -ErrorAction SilentlyContinue
        Get-Content -LiteralPath $purgeErr -ErrorAction SilentlyContinue
    )
    $logPurgeExitCode = [int]$purge.ExitCode
    if ($logPurgeExitCode -ne 0) {
        throw "Impossible de purger les logs au redémarrage. $($logPurgeOutput -join ' | ')"
    }

    # 1. Ensure the permanent service is running on the currently installed code.
    #    If an analysis is active, service_cli leaves the current service untouched.
    $serviceOut = Join-Path $Logs "service-start.out.log"
    $serviceErr = Join-Path $Logs "service-start.err.log"
    $serviceProc = Start-Process -FilePath $Python -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
        -ArgumentList @("-m", "service.service_cli", "restart-if-idle", "--target", "all", "--poll-seconds", "2") `
        -RedirectStandardOutput $serviceOut -RedirectStandardError $serviceErr
    $serviceReloadOutput = @(
        Get-Content -LiteralPath $serviceOut -ErrorAction SilentlyContinue
        Get-Content -LiteralPath $serviceErr -ErrorAction SilentlyContinue
    )
    $serviceReloadExitCode = [int]$serviceProc.ExitCode
    $serviceReloadOutput | Set-Content -LiteralPath (Join-Path $Logs "service-start.log") -Encoding utf8
    if ($serviceReloadExitCode -ne 0) {
        throw "Impossible de charger le service permanent EZS : $($serviceReloadOutput -join ' | ')"
    }

    # Canonical start means controlled restart of owned Caddy proxies per target.
    # Separate stderr from stdout: PowerShell 5.1 can throw on native stderr
    # when ErrorActionPreference is Stop, losing the real Python traceback.
    $caddyResults = @()
    foreach ($target in @("dev", "prod", "lab")) {
        $stdoutPath = Join-Path $Logs ("caddy-start-" + $target + ".out.log")
        $stderrPath = Join-Path $Logs ("caddy-start-" + $target + ".err.log")
        try {
            $proc = Start-Process -FilePath $Python -WorkingDirectory $Root -Wait -PassThru -NoNewWindow `
                -ArgumentList @("-m", "caddy_manager.cli", "restart", "--target", $target) `
                -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
            $output = if (Test-Path -LiteralPath $stdoutPath) {
                Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue
            } else { "" }
            $errorText = if (Test-Path -LiteralPath $stderrPath) {
                Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
            } else { "" }
            $code = [int]$proc.ExitCode
            $ready = ($code -eq 0 -and $output -match "http=True")
            $caddyResults += ("[{0}] exit={1} ready={2}`nstdout: {3}`nstderr: {4}" -f $target, $code, $ready, $output, $errorText)
            if (-not $ready) {
                Add-Content -LiteralPath $ErrLog -Value ("CADDY_START_FAILURE target=" + $target + " exit=" + $code + " details=" + $stderrPath) -Encoding utf8
            }
        }
        catch {
            $detail = $_ | Out-String
            $caddyResults += ("[{0}] launcher_exception: {1}" -f $target, $detail)
            Add-Content -LiteralPath $ErrLog -Value ("CADDY_LAUNCH_EXCEPTION target=" + $target + " " + $detail) -Encoding utf8
        }
    }
    $caddyResults | Set-Content -LiteralPath (Join-Path $Logs "caddy-start.log") -Encoding utf8
    # A failed target is reported explicitly but does not hide diagnostics for other targets.
    if ($caddyResults -match "ready=False|launcher_exception:") {
        Add-Content -LiteralPath $ErrLog -Value "CADDY_RESTART_PARTIAL_FAILURE: see caddy-start.log" -Encoding utf8
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
    $message = "[$stamp] $($_ | Out-String)"

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
