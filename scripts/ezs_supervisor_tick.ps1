# Durable Scheduled Task entrypoint. Does not change desired states.
$ErrorActionPreference = 'Stop'
$root = 'H:\EZS_orchestrator'
$php = 'H:\PHP\php-8.5-x64\php.exe'
$logDir = Join-Path $root 'var\log\supervision'
try {
    if (!(Test-Path -LiteralPath $php -PathType Leaf)) { throw 'EZS_SUPERVISOR_PHP_MISSING' }
    if (!(Test-Path -LiteralPath (Join-Path $root 'bin\console') -PathType Leaf)) { throw 'EZS_SUPERVISOR_CONSOLE_MISSING' }
    if (!(Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Set-Location -LiteralPath $root
    $lines = & $php bin\console ezs:services tick 2>&1
    $code = $LASTEXITCODE
    $stamp = [DateTime]::UtcNow.ToString('o')
    foreach ($line in @($lines)) {
        Add-Content -LiteralPath (Join-Path $logDir 'scheduled-tick.log') -Encoding UTF8 -Value "$stamp $line"
    }
    exit $code
} catch {
    if (!(Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -LiteralPath (Join-Path $logDir 'scheduled-tick.log') -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) ERROR $($_.Exception.Message)"
    exit 1
}
