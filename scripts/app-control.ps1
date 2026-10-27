param(
    [Parameter(Mandatory=$true)][ValidateSet('start','stop','restart','status')][string]$Action,
    [Parameter(Mandatory=$true)][ValidateSet('ezscore-dev')][string]$Application
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root 'runtime\app-control'
$Lock = Join-Path $Runtime 'control.lock'
$BackendScript = 'H:\EZScore_dev\scripts\dev-fastcgi.ps1'
$CaddyCheck = Join-Path $PSScriptRoot 'caddy_dev_shared.ps1'
New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
$mutex = [IO.File]::Open($Lock,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
    function AssertOrchestrator {
        $state = Join-Path $Root 'runtime\v2-dev\processes.json'
        if (-not (Test-Path -LiteralPath $state)) { throw 'APP_CONTROL_ORCHESTRATOR_METADATA_MISSING' }
        $meta = Get-Content -LiteralPath $state -Raw -Encoding UTF8 | ConvertFrom-Json
        $backendPid = [int]$meta.php_pid
        if ($backendPid -le 0) { throw 'APP_CONTROL_ORCHESTRATOR_NOT_OWNED' }
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $backendPid" -ErrorAction SilentlyContinue
        $expected = 'H:\PHP\php-8.5-x64\php-cgi.exe'
        if ($null -eq $proc -or -not [string]::Equals([string]$proc.ExecutablePath,$expected,[StringComparison]::OrdinalIgnoreCase) -or
            [string]$proc.CommandLine -notmatch ' -b 127\.0\.0\.1:8791') { throw 'APP_CONTROL_ORCHESTRATOR_IDENTITY_FAILED' }
        $listener = Get-NetTCPConnection -State Listen -LocalPort 8791 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $listener -or [int]$listener.OwningProcess -ne $backendPid) { throw 'APP_CONTROL_ORCHESTRATOR_BACKEND_MISSING' }
        $result = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/api/v2/environments' -UseBasicParsing -TimeoutSec 8
        if ($result.StatusCode -ne 200) { throw 'APP_CONTROL_ORCHESTRATOR_HTTP_FAILED' }
    }
    if (-not (Test-Path -LiteralPath $BackendScript -PathType Leaf)) { throw 'APP_CONTROL_EZSCORE_DEV_SCRIPT_MISSING' }
    if ($Action -eq 'status') {
        & $BackendScript -Action status
        if (-not $?) { throw 'APP_CONTROL_STATUS_FAILED' }
        exit 0
    }
    AssertOrchestrator
    $caddy = & $CaddyCheck -Action status
    if ($LASTEXITCODE -ne 0 -or [string]$caddy -notmatch '^CADDY_DEV_REUSED PID=\d+$') { throw 'APP_CONTROL_SHARED_CADDY_UNAVAILABLE' }
    if ($Action -eq 'restart') {
        & $BackendScript -Action stop
        if (-not $?) { throw 'APP_CONTROL_STOP_FAILED' }
        & $BackendScript -Action start
        if (-not $?) { throw 'APP_CONTROL_START_FAILED' }
    } else {
        & $BackendScript -Action $Action
        if (-not $?) { throw "APP_CONTROL_ACTION_FAILED $Action" }
    }
    Write-Host "APP_CONTROL_OK APP=$Application ACTION=$Action"
} finally {
    $mutex.Dispose()
}
