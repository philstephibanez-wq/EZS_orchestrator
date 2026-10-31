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
    # A single empty TCP snapshot is not proof that ROOT is absent: the PHP
    # cleaner may be terminating a residual while an active ROOT is stable.
    # Keep the fast path short when a listener is already present.
    $listeners = @(Get-Listeners 8791)
    if ($listeners.Count -gt 0) { return }
    $owned = @(Get-Owned $phpCgi 'php' '')
    if ($owned.Count -gt 0) {
        Write-Event ('ROOT_FASTCGI_NOT_LISTENING_EXISTING_PID=' + ($owned.ProcessId -join ','))
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
    $p = Start-Process -FilePath $phpCgi -ArgumentList @('-b','127.0.0.1:8791') -WorkingDirectory $root -PassThru -WindowStyle Hidden
    Write-Event ('ROOT_FASTCGI_START_PID=' + $p.Id)
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
