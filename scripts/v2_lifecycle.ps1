param([ValidateSet('start','stop','status','repair')][string]$Action)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = Join-Path $root 'runtime\v2-dev'
$stateFile = Join-Path $runtime 'processes.json'
$lockFile = Join-Path $runtime 'lifecycle.lock'
$php = 'H:\PHP\php-8.5-x64\php-cgi.exe'
$caddy = 'H:\Caddy\caddy.exe'
$config = Join-Path $root 'config\caddy\Caddyfile.dev-root-candidate'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Listening([int]$port) {
    return @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function ProcessInfo([int]$processId) {
    if ($processId -le 0) { return $null }
    return Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
}
function Owned([int]$processId, [string]$binary, [string]$signature) {
    $p = ProcessInfo $processId
    if ($null -eq $p) { return $false }
    return [string]::Equals([string]$p.ExecutablePath, $binary, [System.StringComparison]::OrdinalIgnoreCase) -and
        ([string]$p.CommandLine).Contains($signature)
}
function State {
    if (-not (Test-Path -LiteralPath $stateFile)) { return $null }
    return (Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Save-State($value) {
    $bytes = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($stateFile, ($value | ConvertTo-Json -Depth 4), $bytes)
}
function Port-Owned([int]$port, [int]$processId) {
    $listeners = @(Listening $port)
    return ($listeners.Count -eq 1 -and [int]$listeners[0].OwningProcess -eq $processId)
}
function Wait-Port([int]$port, [int]$processId) {
    # Windows may expose a TCP listener before its OwningProcess stabilizes.
    # A transient mismatch must not be reported as a definitive startup failure.
    for ($i = 0; $i -lt 40; $i++) {
        if (Port-Owned $port $processId) { return $true }
        $live = ProcessInfo $processId
        if ($null -eq $live) { return $false }
        Start-Sleep -Milliseconds 250
    }
    return (Port-Owned $port $processId)
}
function Refuse-OtherDevListeners([int]$caddyPid) {
    foreach ($port in @(8502, 8852)) {
        $found = @(Listening $port)
        if ($found.Count -ne 1 -or [int]$found[0].OwningProcess -ne $caddyPid) {
            throw "EZS_STOP_REFUSED_CADDY_DEV_FACADE_OWNER_$port"
        }
    }
    foreach ($port in @(8602, 8701, 8702, 8712, 8862)) {
        if ((@(Listening $port)).Count -gt 0) {
            throw "EZS_GLOBAL_STOP_REQUIRES_DEV_OWNERSHIP_PORT_$port"
        }
    }
}
$lock = $null
try {
    $lock = [System.IO.File]::Open($lockFile, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
} catch {
    throw 'EZS_LIFECYCLE_CONCURRENT_OPERATION'
}
try {
    $s = State
    if ($Action -eq 'status') {
        $phpOk = $false
        $caddyOk = $false
        if ($null -ne $s) {
            $phpOk = (Owned ([int]$s.php_pid) $php '-b 127.0.0.1:8791') -and (Port-Owned 8791 ([int]$s.php_pid))
            $caddyOk = (Owned ([int]$s.caddy_pid) $caddy 'Caddyfile.dev-root-candidate') -and (Port-Owned 8790 ([int]$s.caddy_pid))
        }
        Write-Host "EZS_STATUS php_owned=$phpOk caddy_owned=$caddyOk state_present=$($null -ne $s)"
        return
    }
    if ($Action -eq 'repair') {
        if ($null -eq $s) { throw 'EZS_DEV_REPAIR_REFUSED_NO_STATE' }
        $oldPid = [int]$s.php_pid
        $caddyPid = [int]$s.caddy_pid
        if (-not (Owned $caddyPid $caddy 'Caddyfile.dev-root-candidate') -or
            -not (Port-Owned 8790 $caddyPid) -or -not (Port-Owned 8502 $caddyPid) -or
            -not (Port-Owned 8852 $caddyPid)) {
            throw 'EZS_DEV_REPAIR_REFUSED_CADDY_NOT_VERIFIED'
        }
        if ((Owned $oldPid $php '-b 127.0.0.1:8791') -and (Port-Owned 8791 $oldPid)) {
            Write-Host 'EZS_DEV_REPAIR_NOT_NEEDED'
            return
        }
        # Do not overwrite an occupied port or kill an unidentified/stale PID.
        if ((@(Listening 8791)).Count -gt 0 -or $null -ne (ProcessInfo $oldPid)) {
            throw 'EZS_DEV_REPAIR_REFUSED_PHP_PROCESS_OR_PORT_PRESENT'
        }
        if (-not (Test-Path -LiteralPath $php -PathType Leaf)) { throw 'EZS_DEV_REPAIR_PHP_MISSING' }
        $env:APP_ENV = 'dev'
        $env:APP_DEBUG = '1'
        $env:PHP_FCGI_MAX_REQUESTS = '0'
        $backend = Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:8791' -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if (-not (Wait-Port 8791 ([int]$backend.Id))) {
            if (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791') {
                Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
            }
            throw 'EZS_DEV_REPAIR_FASTCGI_FAILED'
        }
        if (-not (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791')) {
            throw 'EZS_DEV_REPAIR_REFUSED_UNVERIFIED_NEW_PROCESS'
        }
        $s.php_pid = [int]$backend.Id
        Save-State $s
        Write-Host 'EZS_DEV_REPAIR_FASTCGI_OK_CADDY_PRESERVED'
        return
    }
    if ($Action -eq 'stop') {
        if ($null -eq $s) { Write-Host 'EZS_STOP_NO_OWNED_STATE'; return }
        $p = [int]$s.php_pid
        $c = [int]$s.caddy_pid
        if (-not (Owned $p $php '-b 127.0.0.1:8791') -or -not (Port-Owned 8791 $p) -or
            -not (Owned $c $caddy 'Caddyfile.dev-root-candidate') -or -not (Port-Owned 8790 $c)) {
            throw 'EZS_STOP_REFUSED_UNVERIFIED_PROCESS_OWNERSHIP'
        }
        Refuse-OtherDevListeners $c
        Stop-Process -Id $p -ErrorAction Stop
        Stop-Process -Id $c -ErrorAction Stop
        Remove-Item -LiteralPath $stateFile -Force
        Write-Host 'EZS_STOP_OWNED_ORCHESTRATOR_AND_CADDY_OK_PROD_UNTOUCHED'
        return
    }
    if ($null -ne $s) {
        $phpId = [int]$s.php_pid
        $caddyId = [int]$s.caddy_pid
        $healthy = (Owned $phpId $php '-b 127.0.0.1:8791') -and (Port-Owned 8791 $phpId) -and
            (Owned $caddyId $caddy 'Caddyfile.dev-root-candidate') -and (Port-Owned 8790 $caddyId) -and
            (Port-Owned 8502 $caddyId) -and (Port-Owned 8852 $caddyId)
        if (-not $healthy) { throw 'EZS_START_REFUSED_EXISTING_OR_STALE_STATE' }
        Write-Host 'EZS_DEV_ALREADY_RUNNING_VERIFIED'
        return
    }
    if ((@(Listening 8790)).Count -gt 0 -or (@(Listening 8791)).Count -gt 0) {
        throw 'EZS_START_REFUSED_PORT_8790_OR_8791_IN_USE'
    }
    foreach ($path in @($php, $caddy, $config, (Join-Path $root 'vendor\autoload.php'), (Join-Path $root 'public\index.php'))) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "EZS_START_DEPENDENCY_MISSING:$path" }
    }
    & $caddy validate --config $config --adapter caddyfile | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'EZS_START_INVALID_CADDY_CONFIG' }
    $env:APP_ENV = 'dev'
    $env:APP_DEBUG = '1'
    $env:PHP_FCGI_MAX_REQUESTS = '0'
    # Diagnostic hors dépôt : capturer l'erreur native de php-cgi avant son éventuelle sortie.
    $diagnosticDir = Join-Path ([IO.Path]::GetTempPath()) 'ezs-orchestrator'
    New-Item -ItemType Directory -Path $diagnosticDir -Force | Out-Null
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
    $stderrPath = Join-Path $diagnosticDir ("php-cgi-start-" + $stamp + ".stderr.log")
    $stdoutPath = Join-Path $diagnosticDir ("php-cgi-start-" + $stamp + ".stdout.log")
    $backend = Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:8791' -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardError $stderrPath -RedirectStandardOutput $stdoutPath
    if (-not (Wait-Port 8791 ([int]$backend.Id))) {
        $observed = @(Listening 8791)
        $observedPids = ($observed | ForEach-Object { [string]$_.OwningProcess }) -join ','
        $process = ProcessInfo ([int]$backend.Id)
        $alive = $null -ne $process
        $nativeError = ''
        if (Test-Path -LiteralPath $stderrPath) {
            $nativeError = (Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue)
        }
        Write-Host ("EZS_FASTCGI_DIAGNOSTIC launched_pid={0} alive={1} listener_pids={2} stderr_file={3}" -f $backend.Id, $alive, $observedPids, $stderrPath)
        if (-not [string]::IsNullOrWhiteSpace($nativeError)) {
            Write-Host ('EZS_FASTCGI_STDERR: ' + $nativeError.Trim())
        }
        if (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791') {
            Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
        }
        throw 'EZS_START_FASTCGI_FAILED_DIAGNOSTIC_AVAILABLE'
    }
    $edge = $null
    try {
        $edge = Start-Process -FilePath $caddy -ArgumentList @('run','--config',('"' + $config + '"'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if (-not (Wait-Port 8790 ([int]$edge.Id))) { throw 'EZS_START_CADDY_FAILED' }
        Save-State ([pscustomobject]@{ php_pid = [int]$backend.Id; caddy_pid = [int]$edge.Id; started_utc = [DateTime]::UtcNow.ToString('o') })
    } catch {
        if ($null -ne $edge -and (Owned ([int]$edge.Id) $caddy 'Caddyfile.dev-root-candidate')) { Stop-Process -Id $edge.Id -ErrorAction SilentlyContinue }
        if (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791') { Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
        throw
    }
    Write-Host 'EZS_START_ORCHESTRATOR_CADDY_OK_8790_8791'
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
}
