[CmdletBinding()]
param([switch]$DevOnly,[switch]$RootOnly)
# EZS watchdog: HTTP availability for Caddy DEV/PROD; bootstrap ROOT FastCGI.
# Intentionally independent from Symfony, ezs:services, pending and PHPUnit.
$ErrorActionPreference = 'Stop'
$root = 'H:\EZS_orchestrator'
$caddy = 'H:\Caddy\caddy.exe'
$phpCgi = 'H:\PHP\php-8.5-x64\php-cgi.exe'
$runtime = Join-Path $root 'runtime\watchdog'
$logDir = Join-Path $root 'var\log\supervision'
$statePath = Join-Path $runtime 'http-failures.json'
$specs = @(
    @{ Name='dev'; Url='http://127.0.0.1:8790/'; Port=8790; Config=(Join-Path $root 'config\caddy\Caddyfile.dev-lab-assistant-candidate') },
    @{ Name='prod'; Url='http://127.0.0.1:8501/'; Port=8501; Config=(Join-Path $root 'config\caddy\Caddyfile.prod') }
)
if ($DevOnly -and $RootOnly) { throw 'EZS_WATCHDOG_SCOPE_CONFLICT' }
if ($DevOnly) { $specs = @($specs | Where-Object { $_.Name -eq 'dev' }) }
if ($RootOnly) { $specs = @() }
function Write-Event([string]$message) {
    $line = [DateTime]::UtcNow.ToString('o') + ' ' + $message
    Add-Content -LiteralPath (Join-Path $logDir 'watchdog.log') -Value $line -Encoding UTF8
    Write-Output $message
}
function Get-Listeners([int]$port) {
    @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}
function Get-Owned([string]$executable,[string]$kind,[string]$argument) {
    $normExe = $executable.Replace('/','\')
    @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $exe = [string]$_.ExecutablePath
        $cmd = [string]$_.CommandLine
        if ($exe.Replace('/','\') -ine $normExe) { return $false }
        if ($kind -eq 'caddy') {
            # The config is the ownership discriminator. Do not adopt a different Caddy instance.
            return ($cmd -match '(?i)(?:^|\s)run(?:\s|$)' -and
                $cmd.Replace('/','\').IndexOf($argument.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -ge 0)
        }
        return ($cmd -match '(?i)(?:^|\s)"?-b"?\s+"?127\.0\.0\.1:8791"?(?:\s|$)')
    })
}
function Start-Caddy([hashtable]$spec) {
    if (!(Test-Path -LiteralPath $spec.Config -PathType Leaf)) { throw ('EZS_CADDY_CONFIG_MISSING_' + $spec.Name) }
    $args = @('run','--config',$spec.Config,'--adapter','caddyfile')
    $p = Start-Process -FilePath $caddy -ArgumentList $args -WorkingDirectory $root -PassThru -WindowStyle Hidden
    Write-Event ('CADDY_START_' + $spec.Name + ' PID=' + $p.Id)
}
function Test-HttpAnswer([string]$url) {
    try {
        # Any HTTP response, including 502/503, proves Caddy is answering.
        $req = [System.Net.HttpWebRequest][System.Net.WebRequest]::Create($url)
        $req.Timeout = 4000
        $req.ReadWriteTimeout = 4000
        $req.AllowAutoRedirect = $false
        $req.Proxy = $null
        $response = $req.GetResponse()
        try { return $true } finally { $response.Dispose() }
    } catch [System.Net.WebException] {
        if ($null -ne $_.Exception.Response) { $_.Exception.Response.Dispose(); return $true }
        return $false
    } catch { return $false }
}
function Start-RootFastCgi {
    # R1F: only one identified ROOT FastCGI owner may be recovered while port 8791 is listening.
    # Caddy's generic HTTP check intentionally accepts 502; this is a separate Symfony /health probe.
    $healthOk = $false
    try {
        $req = [System.Net.HttpWebRequest][System.Net.WebRequest]::Create('http://127.0.0.1:8790/health')
        $req.Timeout = 3000; $req.ReadWriteTimeout = 3000
        $req.AllowAutoRedirect = $false; $req.Proxy = $null
        $response = $req.GetResponse()
        try {
            if ([int]$response.StatusCode -eq 200) {
                $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
                try {
                    $body = $reader.ReadToEnd() | ConvertFrom-Json -ErrorAction Stop
                    $healthOk = ($body.schema -eq 'ezs.root.health.v1' -and
                        $body.component -eq 'orchestrator-root' -and $body.status -eq 'HEALTHY')
                } finally { $reader.Dispose() }
            }
        } finally { $response.Dispose() }
    } catch { $healthOk = $false }
    $failureFile = Join-Path $runtime 'root-fastcgi-health-failure.json'
    if ($healthOk) {
        if (Test-Path -LiteralPath $failureFile) { Remove-Item -LiteralPath $failureFile -Force }
        Write-Event 'ROOT_HEALTH_OK'
        return
    }
    $nowHealth = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if (!(Test-Path -LiteralPath $failureFile)) {
        $first = @{schema='ezs.root-health-failure.v1';first_failure=$nowHealth} | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText($failureFile,$first,(New-Object System.Text.UTF8Encoding($false)))
        Write-Event 'ROOT_HEALTH_FAILED_FIRST_OBSERVATION'
        # Continue legacy cold boot when no listener/owned process exists.
    }
    $age = 0
    try {
        $failure = Get-Content -LiteralPath $failureFile -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($failure.schema -ne 'ezs.root-health-failure.v1' -or $null -eq $failure.first_failure) { throw 'invalid' }
        $age = $nowHealth - [long]$failure.first_failure
        if ($age -lt 0) { throw 'clock error' }
    } catch { Write-Event 'ROOT_HEALTH_REFUSED_FAILURE_STATE_INVALID'; return }
    $tcpOwners = @(Get-Listeners 8791)
    if ($tcpOwners.Count -gt 0) {
        if ($age -lt 120) { Write-Event ('ROOT_HEALTH_FAILED_WAIT_SECONDS=' + $age); return }
        $desiredFile = Join-Path $root 'runtime\supervision\desired-services.json'
        try {
            $intent = Get-Content -LiteralPath $desiredFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
            if ($intent.schema -ne 'ezs.desired-services.v1' -or $intent.services.root -ne 'RUNNING') { throw 'not running' }
        } catch { Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_INTENT'; return }
        $owned = @(Get-Owned $phpCgi 'php' '')
        if ($owned.Count -ne 1 -or !$owned[0].CreationDate) { Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_IDENTITY'; return }
        $candidate = $owned[0]; $targetPid = [int]$candidate.ProcessId; $created = [string]$candidate.CreationDate
        if (@($tcpOwners | Where-Object { [int]$_.OwningProcess -ne $targetPid }).Count -gt 0) {
            Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_FOREIGN_LISTENER'; return
        }
        Start-Sleep -Seconds 1
        $again = @(Get-Listeners 8791)
        if ($again.Count -eq 0 -or @($again | Where-Object { [int]$_.OwningProcess -ne $targetPid }).Count -gt 0) {
            Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_TCP_CHANGED'; return
        }
        $netstat = & "$env:SystemRoot\System32\netstat.exe" -ano -p tcp
        if ($LASTEXITCODE -ne 0) { Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_NETSTAT'; return }
        $listening = @($netstat | Where-Object { $_ -match '^\s*TCP\s+\S+:8791\s+\S+\s+LISTENING\s+\d+\s*$' })
        if ($listening.Count -eq 0 -or @($listening | Where-Object { $_ -notmatch ('\s+LISTENING\s+' + $targetPid + '\s*$') }).Count -gt 0) {
            Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_NETSTAT_OWNER'; return
        }
        $cooldownFile = Join-Path $runtime 'root-fastcgi-recovery.json'
        if (Test-Path -LiteralPath $cooldownFile) {
            try {
                $prior = Get-Content -LiteralPath $cooldownFile -Raw | ConvertFrom-Json -ErrorAction Stop
                if ($prior.schema -ne 'ezs.root-recovery.v1' -or $null -eq $prior.last_attempt) { throw 'invalid' }
                if ($nowHealth - [long]$prior.last_attempt -lt 300) { Write-Event 'ROOT_HEALTH_RECOVERY_BACKOFF'; return }
            } catch { Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_COOLDOWN'; return }
        }
        $live = @(Get-Owned $phpCgi 'php' '')
        if ($live.Count -ne 1 -or [int]$live[0].ProcessId -ne $targetPid -or [string]$live[0].CreationDate -ne $created) {
            Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_IDENTITY_CHANGED'; return
        }
        try {
            $intent2 = Get-Content -LiteralPath $desiredFile -Raw | ConvertFrom-Json -ErrorAction Stop
            if ($intent2.schema -ne 'ezs.desired-services.v1' -or $intent2.services.root -ne 'RUNNING') { throw 'changed' }
        } catch { Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_INTENT_CHANGED'; return }
        # Recheck listener identity immediately before the only destructive operation.
        $finalOwners = @(Get-Listeners 8791)
        if ($finalOwners.Count -eq 0 -or @($finalOwners | Where-Object { [int]$_.OwningProcess -ne $targetPid }).Count -gt 0) {
            Write-Event 'ROOT_HEALTH_RECOVERY_REFUSED_FINAL_TCP'; return
        }
        $payload = @{schema='ezs.root-recovery.v1';last_attempt=$nowHealth;pid=$targetPid} | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText($cooldownFile,$payload,(New-Object System.Text.UTF8Encoding($false)))
        Stop-Process -Id $targetPid -Force -ErrorAction Stop
        Write-Event ('ROOT_HEALTH_RECOVERY_STOP_PID=' + $targetPid)
        # Cold boot remains the responsibility of the existing next watchdog tick.
        return
    }

    # A single empty TCP snapshot is not proof that ROOT is absent: the PHP
    # cleaner may be terminating a residual while an active ROOT is stable.
    # Keep the fast path short when a listener is already present.
    $listeners = @(Get-Listeners 8791)
    if ($listeners.Count -gt 0) { return }
    $owned = @(Get-Owned $phpCgi 'php' '')
    if ($owned.Count -gt 0) {
        # Confirm operator intent before any destructive action. Missing or invalid state means refusal.
        $desiredFile = Join-Path $root 'runtime\supervision\desired-services.json'
        if (!(Test-Path -LiteralPath $desiredFile -PathType Leaf)) {
            Write-Event 'ROOT_RECOVERY_REFUSED_DESIRED_STATE_MISSING'
            return
        }
        try {
            $intent = Get-Content -LiteralPath $desiredFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
            if ($intent.schema -ne 'ezs.desired-services.v1' -or $intent.services.root -ne 'RUNNING') {
                Write-Event 'ROOT_RECOVERY_REFUSED_NOT_DESIRED_RUNNING'
                return
            }
        } catch { Write-Event 'ROOT_RECOVERY_REFUSED_DESIRED_STATE_INVALID'; return }
        # Exactly one WMI-owned candidate, with stable creation time. No foreign process can be adopted.
        if ($owned.Count -ne 1 -or !$owned[0].CreationDate) {
            Write-Event 'ROOT_RECOVERY_REFUSED_IDENTITY_AMBIGUOUS'
            return
        }
        $candidate = $owned[0]
        $pidToStop = [int]$candidate.ProcessId
        $creation = [string]$candidate.CreationDate
        # Two independent, bounded snapshots must agree that 8791 is not listening.
        $netstat = & "$env:SystemRoot\System32\netstat.exe" -ano -p tcp
        if ($LASTEXITCODE -ne 0) { Write-Event 'ROOT_RECOVERY_REFUSED_NETSTAT_FAILED'; return }
        $rootListening = @($netstat | Where-Object { $_ -match '^\s*TCP\s+\S+:8791\s+\S+\s+LISTENING\s+\d+\s*$' })
        if ($rootListening.Count -gt 0) {
            # Snapshot evidence: only local endpoint, TCP state and PID; no remote peer or secret.
            foreach ($entry in $rootListening) {
                if ($entry -match '^\s*TCP\s+(\S+:8791)\s+\S+\s+(LISTENING)\s+(\d+)\s*$') {
                    Write-Event ('ROOT_RECOVERY_LISTENER_EVIDENCE endpoint=' + $Matches[1] + ' state=' + $Matches[2] + ' pid=' + $Matches[3])
                }
            }
            Write-Event 'ROOT_RECOVERY_REFUSED_LISTENER_NETSTAT'
            return
        }
        Start-Sleep -Seconds 1
        if ((@(Get-Listeners 8791)).Count -gt 0) { Write-Event 'ROOT_RECOVERY_REFUSED_LISTENER_TCP'; return }
        $second = & "$env:SystemRoot\System32\netstat.exe" -ano -p tcp
        if ($LASTEXITCODE -ne 0 -or @($second | Where-Object { $_ -match '^\s*TCP\s+\S+:8791\s+\S+\s+LISTENING\s+\d+\s*$' }).Count -gt 0) {
            Write-Event 'ROOT_RECOVERY_REFUSED_SECOND_NETSTAT'
            return
        }
        # A durable cooldown also applies when a prior attempt failed or the task restarted.
        $cooldownFile = Join-Path $runtime 'root-fastcgi-recovery.json'
        $nowSec = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if (Test-Path -LiteralPath $cooldownFile) {
            try {
                $prior = Get-Content -LiteralPath $cooldownFile -Raw | ConvertFrom-Json -ErrorAction Stop
                if ($prior.schema -ne 'ezs.root-recovery.v1' -or $null -eq $prior.last_attempt) { throw 'invalid' }
                if ($nowSec - [long]$prior.last_attempt -lt 300) { Write-Event 'ROOT_RECOVERY_BACKOFF'; return }
            } catch { Write-Event 'ROOT_RECOVERY_REFUSED_COOLDOWN_STATE_INVALID'; return }
        }
        # Reattest identity, TCP and intent immediately before Stop-Process.
        $live = @(Get-Owned $phpCgi 'php' '')
        $same = @($live | Where-Object { [int]$_.ProcessId -eq $pidToStop -and [string]$_.CreationDate -eq $creation })
        if ($live.Count -ne 1 -or $same.Count -ne 1 -or (@(Get-Listeners 8791)).Count -gt 0) {
            Write-Event 'ROOT_RECOVERY_REFUSED_REATTESTATION'
            return
        }
        try {
            $intent2 = Get-Content -LiteralPath $desiredFile -Raw | ConvertFrom-Json -ErrorAction Stop
            if ($intent2.schema -ne 'ezs.desired-services.v1' -or $intent2.services.root -ne 'RUNNING') { throw 'intent changed' }
        } catch { Write-Event 'ROOT_RECOVERY_REFUSED_DESIRED_CHANGED'; return }
        $payload = @{schema='ezs.root-recovery.v1';last_attempt=$nowSec;pid=$pidToStop} | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText($cooldownFile, $payload, (New-Object System.Text.UTF8Encoding($false)))
        Stop-Process -Id $pidToStop -Force -ErrorAction Stop
        Write-Event ('ROOT_RECOVERY_STOP_CONFIRMED_PID=' + $pidToStop)
        Start-Sleep -Seconds 1
        # Never create another instance until the previous PID is gone and 8791 is free.
        if ($null -ne (Get-Process -Id $pidToStop -ErrorAction SilentlyContinue) -or (@(Get-Listeners 8791)).Count -gt 0) {
            Write-Event 'ROOT_RECOVERY_FAILED_OLD_PROCESS_OR_PORT_REMAINS'
            throw 'ROOT_RECOVERY_FAILED_OLD_PROCESS_OR_PORT_REMAINS'
        }
        # Existing cold-boot path will be used at next tick, after bounded cooldown.
        Write-Event 'ROOT_RECOVERY_STOPPED_NEXT_TICK_BOOT'
        return
    }

    # Cold boot only: two independent snapshots one second apart, and a
    # second TCP enumeration via netstat. A probe error refuses the spawn.
    Start-Sleep -Seconds 1
    $listeners = @(Get-Listeners 8791)
    $owned = @(Get-Owned $phpCgi 'php' '')
    if ($listeners.Count -gt 0 -or $owned.Count -gt 0) {
        Write-Event 'ROOT_FASTCGI_BOOT_ABORTED_CHANGED_OBSERVATION'
        return
    }
    $netstat = & "$env:SystemRoot\System32\netstat.exe" -ano -p tcp
    if ($LASTEXITCODE -ne 0) { throw 'EZS_ROOT_NETSTAT_UNAVAILABLE' }
    $occupied = @($netstat | Where-Object {
        $_ -match '^\s*TCP\s+127\.0\.0\.1:8791\s+\S+\s+LISTENING\s+\d+\s*$' -or
        $_ -match '^\s*TCP\s+0\.0\.0\.0:8791\s+\S+\s+LISTENING\s+\d+\s*$' -or
        $_ -match '^\s*TCP\s+\[::\]:8791\s+\S+\s+LISTENING\s+\d+\s*$'
    })
    if ($occupied.Count -gt 0) {
        Write-Event 'ROOT_FASTCGI_BOOT_ABORTED_NETSTAT_LISTENER'
        return
    }
    # Recheck after netstat as the final time-of-check before process start.
    if ((@(Get-Listeners 8791)).Count -gt 0 -or (@(Get-Owned $phpCgi 'php' '')).Count -gt 0) {
        Write-Event 'ROOT_FASTCGI_BOOT_ABORTED_FINAL_CHECK'
        return
    }
    # L'environnement Symfony est propre au FastCGI ROOT et ne doit pas contaminer Caddy/PROD.
    # Les variables du watchdog sont restaurees meme si Start-Process echoue.
    $previousAppEnv = [Environment]::GetEnvironmentVariable('APP_ENV', 'Process')
    $previousAppDebug = [Environment]::GetEnvironmentVariable('APP_DEBUG', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('APP_ENV', 'dev', 'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG', '1', 'Process')
        $p = Start-Process -FilePath $phpCgi -ArgumentList @('-b','127.0.0.1:8791') -WorkingDirectory $root -PassThru -WindowStyle Hidden
    } finally {
        [Environment]::SetEnvironmentVariable('APP_ENV', $previousAppEnv, 'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG', $previousAppDebug, 'Process')
    }
    Write-Event ('ROOT_FASTCGI_START_PID=' + $p.Id + ' APP_ENV=dev APP_DEBUG=1')
}
if (!(Test-Path $runtime)) { New-Item -ItemType Directory -Force -Path $runtime | Out-Null }
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$mutex = New-Object System.Threading.Mutex($false, 'Local\EZS_WATCHDOG_BOOT_SINGLETON')
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (!$locked) { Write-Event 'WATCHDOG_ALREADY_RUNNING'; return }
    if (!(Test-Path $caddy -PathType Leaf)) { throw 'EZS_CADDY_MISSING' }
    if (!(Test-Path $phpCgi -PathType Leaf)) { throw 'EZS_ROOT_FASTCGI_MISSING' }
    $state = @{}
    if (Test-Path $statePath) {
        $old = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        foreach ($p in $old.PSObject.Properties) { $state[$p.Name] = [long]$p.Value }
    }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($spec in $specs) {
        try {
            $name = $spec.Name
            if (Test-HttpAnswer $spec.Url) {
                $state.Remove($name)
                Write-Event ('CADDY_HTTP_OK_' + $name)
                continue
            }
            if (!$state.ContainsKey($name)) { $state[$name] = $now }
            $elapsed = $now - [long]$state[$name]
            $owned = Get-Owned $caddy 'caddy' $spec.Config
            $listeners = Get-Listeners $spec.Port
            if ($listeners.Count -gt 0 -and $owned.Count -eq 0) {
                Write-Event ('CADDY_FOREIGN_LISTENER_' + $name)
                continue
            }
            if ($owned.Count -eq 0 -and $listeners.Count -eq 0) {
                # Cold boot / killed process: start immediately; no pending gate.
                Start-Caddy $spec
                continue
            }
            if ($elapsed -lt 60) { Write-Event ('CADDY_HTTP_DOWN_' + $name + '_SECONDS=' + $elapsed); continue }
            # DEV: an HTTP timeout alone does not attest a dead Caddy process.
            # Never kill a still-identified Caddy DEV on that evidence alone.
            if ($name -eq 'dev' -and $owned.Count -gt 0) {
                Write-Event ('CADDY_DEV_HTTP_TIMEOUT_OWNED_PROCESS_NO_STOP_SECONDS=' + $elapsed)
                continue
            }
            # A non-responding owned process can be forcibly recycled after 60 s.
            # Never kill a PID unless its current executable/command still match.
            foreach ($process in $owned) {
                $pidToStop = [int]$process.ProcessId
                $live = @(Get-Owned $caddy 'caddy' $spec.Config | Where-Object { $_.ProcessId -eq $pidToStop })
                if ($live.Count -ne 1) { throw ('EZS_CADDY_IDENTITY_CHANGED_' + $name) }
                Stop-Process -Id $pidToStop -Force -ErrorAction Stop
                Write-Event ('CADDY_STOP_UNHEALTHY_' + $name + '_PID=' + $pidToStop)
            }
            Start-Caddy $spec
            $state[$name] = $now
        } catch {
            Write-Event ('CADDY_ERROR_' + $spec.Name + ' ' + $_.Exception.Message)
        }
    }
    try { Start-RootFastCgi } catch { Write-Event ('ROOT_FASTCGI_ERROR ' + $_.Exception.Message) }
    $json = ConvertTo-Json -InputObject $state -Compress
    $tmp = $statePath + '.tmp'
    [System.IO.File]::WriteAllText($tmp,$json,(New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $statePath -Force
} catch {
    Write-Event ('WATCHDOG_ERROR ' + $_.Exception.Message)
    throw
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
