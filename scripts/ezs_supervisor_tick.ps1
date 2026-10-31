# Root watchdog and existing supervisor, scheduled by the pre-existing task.
# Does not stop processes, does not change desired service state.
$ErrorActionPreference = 'Stop'
$root = 'H:\EZS_orchestrator'
$php = 'H:\PHP\php-8.5-x64\php.exe'
$logDir = Join-Path $root 'var\log\supervision'
try {
    if (!(Test-Path -LiteralPath $php -PathType Leaf)) { throw 'EZS_SUPERVISOR_PHP_MISSING' }
    if (!(Test-Path -LiteralPath (Join-Path $root 'bin\console') -PathType Leaf)) { throw 'EZS_SUPERVISOR_CONSOLE_MISSING' }
    if (!(Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Set-Location -LiteralPath $root

    # HTTP probe must not run unit tests or assume a TCP listener proves readiness.
    $httpStatus = 0
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/' -UseBasicParsing -TimeoutSec 4 -MaximumRedirection 0
        $httpStatus = [int]$response.StatusCode
    } catch {
        if ($null -ne $_.Exception.Response) {
            $httpStatus = [int]$_.Exception.Response.StatusCode
        }
    }
    # Read-only desired state through the existing Symfony command, not by guessing.
    $intentLines = & $php bin\console ezs:services status 2>&1
    $intentCode = $LASTEXITCODE
    if ($intentCode -ne 0) { throw "EZS_DESIRED_STATUS_FAILED_$intentCode" }
    $rootWanted = @($intentLines | ForEach-Object { "$_" }) -contains 'root=RUNNING'
    $rootStopped = @($intentLines | ForEach-Object { "$_" }) -contains 'root=STOPPED'
    if (!$rootWanted -and !$rootStopped) { throw 'EZS_DESIRED_ROOT_UNKNOWN' }
    $health = if (!$rootWanted) { 'ROOT_STOPPED_BY_OPERATOR' } elseif ($httpStatus -eq 200) { 'ROOT_HEALTHY' } else { 'ROOT_RECOVERY_REQUIRED' }
    $stamp = [DateTime]::UtcNow.ToString('o')
    Add-Content -LiteralPath (Join-Path $logDir 'watchdog-health.log') -Encoding UTF8 -Value "$stamp $health HTTP=$httpStatus"

    # The existing tick supervises all groups and safely attempts ROOT recovery if desired.
    # It performs strict PID/command/creation-time/port checks; no unsafe force kill.
    $lines = & $php bin\console ezs:services tick 2>&1
    $code = $LASTEXITCODE
    foreach ($line in @($lines)) {
        Add-Content -LiteralPath (Join-Path $logDir 'scheduled-tick.log') -Encoding UTF8 -Value "$stamp $line"
    }
    exit $code
} catch {
    if (!(Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -LiteralPath (Join-Path $logDir 'scheduled-tick.log') -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) ERROR $($_.Exception.Message)"
    exit 1
}
