$ErrorActionPreference = 'Stop'
# Contract: STOP Orchestrator forces PROD maintenance, verifies HTTP 503, then stops DEV only.
# Gateway PROD and EZScore PROD processes must remain alive.
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$php='H:\PHP\php-8.5-x64\php.exe'
$service=Join-Path $root 'src\Module\Infrastructure\ProdModeService.php'
if(-not (Test-Path -LiteralPath $php -PathType Leaf)){throw 'EZS_STOP_MAINTENANCE_PHP_MISSING'}
if(-not (Test-Path -LiteralPath $service -PathType Leaf)){throw 'EZS_STOP_MAINTENANCE_SERVICE_MISSING'}
$entry=Join-Path $root 'bin\prod_mode.php'
if(-not (Test-Path -LiteralPath $entry -PathType Leaf)){throw 'EZS_STOP_MAINTENANCE_ENTRY_MISSING'}
& $php $entry maintenance
if($LASTEXITCODE -ne 0){throw 'EZS_STOP_REFUSED_PROD_MAINTENANCE_UNCONFIRMED'}
Write-Host 'EZS_STOP_PROD_MAINTENANCE_CONFIRMED'
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
if (-not $?) { throw 'EZS_DEV_STOP_FAILED_PROD_MAINTENANCE_PRESERVED' }
