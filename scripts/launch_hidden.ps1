$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$Python = "H:\Python\pythoncore-3.14-64\python.exe"
$ControlCenterUrl = "http://127.0.0.1:8700/"
$OutLog = Join-Path $Logs "control-center.log"
$ErrLog = Join-Path $Logs "control-center-error.log"

function Test-Port8700 {
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $iar = $c.BeginConnect("127.0.0.1", 8700, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne(300)) {
            $c.Close()
            return $false
        }
        $c.EndConnect($iar)
        $c.Close()
        return $true
    }
    catch {
        return $false
    }
}

$serviceStatus = & $Python -m service.service_cli status 2>&1
if ($LASTEXITCODE -ne 0 -or ($serviceStatus -join "`n") -notmatch "SERVICE:\s+running") {
    & $Python -m service.service_cli start --target all --poll-seconds 2 *> (Join-Path $Logs "service-start.log")
}

if (-not (Test-Port8700)) {
    $startScript = Join-Path $Root "scripts\start_control_center.ps1"

    Start-Process powershell.exe `
        -WindowStyle Hidden `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$startScript`""
        ) `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog | Out-Null

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 200
        if (Test-Port8700) { break }
    }
}

if (Test-Port8700) {
    Start-Process $ControlCenterUrl
}
else {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $ErrLog -Value "[$stamp] Control Center did not open port 8700."
}
