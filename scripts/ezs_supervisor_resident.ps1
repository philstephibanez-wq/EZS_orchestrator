# ROOT-only resident; delegates every cycle to the canonical watchdog tick.
[CmdletBinding()]
param([ValidateRange(15,300)][int]$IntervalSeconds = 60)
$ErrorActionPreference = 'Stop'
$root = 'H:\EZS_orchestrator'
$tick = Join-Path $root 'scripts\ezs_supervisor_tick.ps1'
$logDir = Join-Path $root 'var\log\supervision'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$mutex = [System.Threading.Mutex]::new($false, 'Local\EZS_ROOT_RESIDENT_SINGLETON')
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'EZS_ROOT_RESIDENT_ALREADY_RUNNING' }
    if (-not (Test-Path -LiteralPath $tick -PathType Leaf)) { throw 'EZS_ROOT_RESIDENT_TICK_MISSING' }
    while ($true) {
        $start = [DateTime]::UtcNow
        try {
            & $tick -RootOnly
            if (-not $?) { throw 'EZS_ROOT_TICK_FAILED' }
        } catch {
            $stamp = [DateTime]::UtcNow.ToString('o')
            Add-Content -LiteralPath (Join-Path $logDir 'watchdog-resident.log') -Value "$stamp ROOT_RESIDENT_TICK_ERROR $($_.Exception.Message)" -Encoding UTF8
        }
        $elapsed = [int]([DateTime]::UtcNow - $start).TotalSeconds
        Start-Sleep -Seconds ([Math]::Max(1, $IntervalSeconds - $elapsed))
    }
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
