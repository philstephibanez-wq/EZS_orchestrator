[CmdletBinding()]
param([switch]$Once)
# Independent ROOT-only liveness / ownership supervisor. Classic FrankenPHP only.
$ErrorActionPreference='Stop'
$root='H:\EZS_orchestrator'
$exe='H:\FRANKENPHP\bin\frankenphp.exe'
$runtime=Join-Path $root 'runtime\watchdog'
$logDir=Join-Path $root 'var\log\supervision'
$ownerFile=Join-Path $runtime 'root-frankenphp-owner.json'
$failFile=Join-Path $runtime 'root-frankenphp-failure.json'
$intentFile=Join-Path $root 'runtime\supervision\desired-services.json'
$health='http://127.0.0.1:8790/health'
foreach($dir in @($runtime,$logDir)) {
    if (!(Test-Path -LiteralPath $dir -PathType Container)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}
function Log([string]$event,[string]$detail='') {
    $json=ConvertTo-Json -Compress -InputObject ([ordered]@{schema='ezs.root.watchdog.v1';utc=[DateTime]::UtcNow.ToString('o');event=$event;detail=$detail})
    [IO.File]::AppendAllText((Join-Path $logDir 'root-frankenphp-watchdog.jsonl'),$json+"`n",(New-Object Text.UTF8Encoding($false)))
    Write-Output ($event+' '+$detail)
}
function Read-State([string]$path) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
    Get-Content -LiteralPath $path -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
}
function Save-State([string]$path,$value) {
    $temp=$path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    try {
        $str=ConvertTo-Json -Compress -Depth 5 -InputObject $value
        [IO.File]::WriteAllText($temp,$str+"`n",(New-Object Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temp -Destination $path -Force -ErrorAction Stop
    } finally { if (Test-Path -LiteralPath $temp) {Remove-Item -LiteralPath $temp -Force} }
}
function Get-Intent {
    $s=Read-State $intentFile
    if ($null -eq $s -or $s.schema -ne 'ezs.desired-services.v1' -or
        [string]$s.services.root -notin @('RUNNING','STOPPED')) {throw 'ROOT_INTENT_INVALID'}
    [string]$s.services.root
}
function Get-Listeners {
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 8790 })
}
function Get-RootProcesses {
    @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        [string]$_.ExecutablePath -ieq $exe -and
        [string]$_.CommandLine -match '(?i)(?:^|\s)php-server(?:\s|$)' -and
        [string]$_.CommandLine -match '(?i)--listen(?:\s+|=)127\.0\.0\.1:8790(?:\s|$)' -and
        [string]$_.CommandLine -match '(?i)--root(?:\s+|=)["'']?H:[\\/]+EZS_orchestrator[\\/]+public(?:["'']|\s|$)'
    })
}
function Matches-Owner($owner,$p) {
    ($null -ne $owner -and $owner.schema -eq 'ezs.root.frankenphp.owner.v1' -and
        [int]$owner.pid -eq [int]$p.ProcessId -and
        [string]$owner.creation -eq [string]$p.CreationDate -and
        [string]$p.ExecutablePath -ieq $exe)
}
function Test-Rest {
    try {
        $r=Invoke-WebRequest -Uri $health -UseBasicParsing -TimeoutSec 4 -ErrorAction Stop
        $j=$r.Content | ConvertFrom-Json -ErrorAction Stop
        $v=(Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw -ErrorAction Stop).Trim()
        ([int]$r.StatusCode -eq 200 -and $j.schema -eq 'ezs.root.health.v1' -and
            $j.component -eq 'orchestrator-root' -and $j.status -eq 'HEALTHY' -and $j.version -eq $v)
    } catch { $false }
}
$mutex=New-Object Threading.Mutex($false,'Local\EZS_ROOT_FRANKENPHP_TICK')
$locked=$false
try {
    try {$locked=$mutex.WaitOne(0)} catch [Threading.AbandonedMutexException] {$locked=$true}
    if (!$locked) { Log 'TICK_ALREADY_RUNNING';return }
    if ((Get-Intent) -ne 'RUNNING') {Log 'ROOT_INTENTION_STOPPED_NO_ACTION';return}
    if (!(Test-Path -LiteralPath $exe -PathType Leaf)) {throw 'FRANKENPHP_MISSING'}
    $all=@(Get-RootProcesses)
    $ports=@(Get-Listeners)
    $owner=Read-State $ownerFile
    if ($null -ne $owner -and $owner.schema -ne 'ezs.root.frankenphp.owner.v1') {throw 'ROOT_OWNER_INVALID'}
    $ok=Test-Rest
    if ($ok -and $ports.Count -eq 1) {
        if ($all.Count -eq 1 -and (Matches-Owner $owner $all[0]) -and
            [int]$ports[0].OwningProcess -eq [int]$all[0].ProcessId) {
            if (Test-Path -LiteralPath $failFile) {Remove-Item -LiteralPath $failFile -Force}
            Log 'ROOT_HEALTHY_OWNED' ('pid='+$all[0].ProcessId)
        } else {Log 'ROOT_HEALTHY_UNMANAGED_NO_ADOPTION'}
        return
    }
    if ($ports.Count -gt 1 -or $all.Count -gt 1) {Log 'ROOT_REFUSED_AMBIGUOUS_OWNERSHIP';return}
    if ($ports.Count -eq 1) {
        if ($all.Count -ne 1 -or !(Matches-Owner $owner $all[0]) -or
            [int]$ports[0].OwningProcess -ne [int]$all[0].ProcessId) {
            Log 'ROOT_REFUSED_FOREIGN_LISTENER';return
        }
        $now=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $fail=Read-State $failFile
        if ($null -eq $fail) {
            Save-State $failFile @{schema='ezs.root.frankenphp.failure.v1';first=$now}
            Log 'ROOT_HEALTH_FAILED_WAIT';return
        }
        if ($fail.schema -ne 'ezs.root.frankenphp.failure.v1' -or $null -eq $fail.first) {throw 'ROOT_FAILURE_STATE_INVALID'}
        if ($now-[long]$fail.first -lt 60) {Log 'ROOT_UNHEALTHY_WAIT';return}
        if ($now-[long]$fail.first -gt 900) {Log 'ROOT_UNHEALTHY_STALE_REFUSED';return}
        $again=@(Get-RootProcesses);$tcp=@(Get-Listeners)
        if ((Get-Intent) -ne 'RUNNING' -or $again.Count -ne 1 -or
            !(Matches-Owner $owner $again[0]) -or $tcp.Count -ne 1 -or
            [int]$tcp[0].OwningProcess -ne [int]$owner.pid -or (Test-Rest)) {
            Log 'ROOT_STOP_REFUSED_REATTESTATION';return
        }
        Stop-Process -Id ([int]$owner.pid) -Force -ErrorAction Stop
        Save-State $failFile @{schema='ezs.root.frankenphp.failure.v1';first=$now;last_stop=$now}
        Log 'ROOT_OWNED_UNHEALTHY_STOPPED_NEXT_CYCLE';return
    }
    if ($all.Count -ne 0) {Log 'ROOT_REFUSED_PROCESS_WITHOUT_LISTENER';return}
    if ($null -ne $owner) {
        # No PID reuse or orphan adoption; require disappearance before a replacement launch.
        $old=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$owner.pid) -ErrorAction Stop
        if ($null -ne $old) {Log 'ROOT_REFUSED_PRIOR_PID_STILL_EXISTS';return}
    }
    if ((Get-Intent) -ne 'RUNNING' -or @(Get-Listeners).Count -ne 0) {Log 'ROOT_REFUSED_BOOT_RECHECK';return}
    $now=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $fail=Read-State $failFile
    if ($null -ne $fail) {
        if ($fail.schema -ne 'ezs.root.frankenphp.failure.v1') {throw 'ROOT_FAILURE_STATE_INVALID'}
        if ($null -ne $fail.last_stop -and $now-[long]$fail.last_stop -lt 300) {Log 'ROOT_RESTART_BACKOFF';return}
    }
    $oldEnv=[Environment]::GetEnvironmentVariable('APP_ENV','Process')
    $oldDbg=[Environment]::GetEnvironmentVariable('APP_DEBUG','Process')
    try {
        [Environment]::SetEnvironmentVariable('APP_ENV','dev','Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG','1','Process')
        $spawn=Start-Process -FilePath $exe -ArgumentList 'php-server --listen 127.0.0.1:8790 --root H:\EZS_orchestrator\public' -WorkingDirectory $root -WindowStyle Hidden -PassThru -ErrorAction Stop
    } finally {
        [Environment]::SetEnvironmentVariable('APP_ENV',$oldEnv,'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG',$oldDbg,'Process')
    }
    $p=@(Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$spawn.Id) -ErrorAction Stop)
    if ($p.Count -ne 1 -or [string]$p[0].ExecutablePath -ine $exe) {Log 'ROOT_SPAWN_UNATTESTED';throw 'ROOT_SPAWN_UNATTESTED'}
    Save-State $ownerFile @{schema='ezs.root.frankenphp.owner.v1';pid=[int]$spawn.Id;creation=[string]$p[0].CreationDate}
    Log 'ROOT_SPAWN_OWNED' ('pid='+$spawn.Id)
    Start-Sleep -Seconds 2
    if (Test-Rest) {Log 'ROOT_RECOVERED_HTTP_OK'} else {Log 'ROOT_BOOT_HTTP_PENDING'}
} catch {
    Log 'ROOT_WATCHDOG_FAILED' $_.Exception.Message
    throw
} finally {
    if ($locked) {$mutex.ReleaseMutex()}
    $mutex.Dispose()
}
