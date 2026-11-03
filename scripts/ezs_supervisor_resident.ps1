# ROOT resident owns the one-time EZS site initialization on its own startup.
[CmdletBinding()]
param([ValidateRange(15,300)][int]$IntervalSeconds=60)
$ErrorActionPreference='Stop'
$root='H:\EZS_orchestrator'
$watchdog=Join-Path $root 'scripts\ezs_root_frankenphp_watchdog.ps1'
$boot=Join-Path $root 'scripts\ezs_boot_sites_r7.ps1'
$logDir=Join-Path $root 'var\log\supervision'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$mutex=New-Object Threading.Mutex($false,'Local\EZS_ROOT_RESIDENT_SINGLETON')
$locked=$false
$attempted=$false
try {
    try {$locked=$mutex.WaitOne(0)} catch [Threading.AbandonedMutexException] {$locked=$true}
    if (!$locked) {throw 'EZS_ROOT_RESIDENT_ALREADY_RUNNING'}
    if (!(Test-Path -LiteralPath $watchdog -PathType Leaf)) {throw 'ROOT_FRANKENPHP_WATCHDOG_MISSING'}
    if (!(Test-Path -LiteralPath $boot -PathType Leaf)) {throw 'EZS_SITE_BOOT_R7_MISSING'}
    while ($true) {
        $start=[DateTime]::UtcNow
        try {
            & $watchdog -Once
            if (!$?) {throw 'ROOT_FRANKENPHP_WATCHDOG_FAILED'}
        } catch {
            $utc=[DateTime]::UtcNow.ToString('o')
            Add-Content -LiteralPath (Join-Path $logDir 'watchdog-resident.log') -Value "$utc ROOT_RESIDENT_TICK_ERROR $($_.Exception.Message)" -Encoding UTF8
        }
        if (!$attempted) {
            # ROOT must answer health before the first and only site boot attempt.
            try {
                $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8790/health' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
                if ([int]$r.StatusCode -eq 200) {
                    $attempted=$true  # No retry in this resident lifetime after failure.
                    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $boot -Action Boot | Out-Null
                    if($LASTEXITCODE -ne 0){throw 'EZS_R7_INITIAL_SITE_BOOT_PARTIAL'}
                }
            } catch {
                $utc=[DateTime]::UtcNow.ToString('o')
                Add-Content -LiteralPath (Join-Path $logDir 'watchdog-resident.log') -Value "$utc SITE_BOOT_R7 $($_.Exception.Message)" -Encoding UTF8
            }
        }
        $elapsed=[int]([DateTime]::UtcNow-$start).TotalSeconds
        Start-Sleep -Seconds ([Math]::Max(1,$IntervalSeconds-$elapsed))
    }
} finally {
    if ($locked) {$mutex.ReleaseMutex()}
    $mutex.Dispose()
}
