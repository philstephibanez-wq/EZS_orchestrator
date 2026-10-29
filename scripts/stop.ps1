# Embedded maintained lifecycle helpers; only start.ps1/stop.ps1 are entry points.
function Invoke-EzsRootLifecycle {
param([ValidateSet('start','stop','status','repair')][string]$Action)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = Join-Path $root 'runtime\v2-dev'
$stateFile = Join-Path $runtime 'processes.json'
$lockFile = Join-Path $runtime 'lifecycle.lock'
$php = 'H:\PHP\php-8.5-x64\php-cgi.exe'
$caddy = 'H:\Caddy\caddy.exe'
$config = Join-Path $root 'config\caddy\Caddyfile.dev-lab-assistant-candidate'
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
function OwnedDevCaddy([int]$processId) {
    return (Owned $processId $caddy 'Caddyfile.dev-root-candidate') -or
        (Owned $processId $caddy 'Caddyfile.dev-lab-assistant-candidate')
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
            $caddyOk = (OwnedDevCaddy ([int]$s.caddy_pid)) -and (Port-Owned 8790 ([int]$s.caddy_pid))
        }
        Write-Host "EZS_STATUS php_owned=$phpOk caddy_owned=$caddyOk state_present=$($null -ne $s)"
        return
    }
    if ($Action -eq 'repair') {
        if ($null -eq $s) { throw 'EZS_DEV_REPAIR_REFUSED_NO_STATE' }
        $oldPid = [int]$s.php_pid
        $caddyPid = [int]$s.caddy_pid
        if (-not (OwnedDevCaddy $caddyPid) -or
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
        if ($null -eq $s) {
            foreach ($port in @(8790,8791,8502,8852)) {
                if (@(Listening $port).Count -gt 0) { throw 'EZS_DEV_STOP_REFUSED_UNTRACKED_PORT' }
            }
            Write-Host 'EZS_DEV_ROOT_ALREADY_STOPPED'
            return
        }
        $p = [int]$s.php_pid
        $c = [int]$s.caddy_pid
        # Vérifier l'identité des processus et l'absence de listener étranger.
        # Un composant peut avoir perdu un port après un démarrage partiel.
        $caddyProcess = ProcessInfo $c
        $phpProcess = ProcessInfo $p
        $caddyIdentity = ($c -gt 0 -and (OwnedDevCaddy $c))
        $phpIdentity = ($p -gt 0 -and (Owned $p $php '-b 127.0.0.1:8791'))
        foreach ($port in @(8790,8502,8852)) {
            $listeners = @(Listening $port)
            foreach ($listener in $listeners) {
                if (-not $caddyIdentity -or [int]$listener.OwningProcess -ne $c) {
                    throw "EZS_DEV_STOP_REFUSED_FOREIGN_CADDY_PORT_$port"
                }
            }
        }
        foreach ($listener in @(Listening 8791)) {
            if (-not $phpIdentity -or [int]$listener.OwningProcess -ne $p) {
                throw 'EZS_DEV_STOP_REFUSED_FOREIGN_FASTCGI_PORT_8791'
            }
        }
        if ($null -ne $caddyProcess -and -not $caddyIdentity) {
            throw 'EZS_DEV_STOP_REFUSED_CADDY_PID_REUSED'
        }
        if ($null -ne $phpProcess -and -not $phpIdentity) {
            throw 'EZS_DEV_STOP_REFUSED_FASTCGI_PID_REUSED'
        }
        if ($phpIdentity) {
            Stop-Process -Id $p -ErrorAction Stop
            for ($attempt=0; $attempt -lt 40; $attempt++) {
                if ($null -eq (ProcessInfo $p) -and @(Listening 8791).Count -eq 0) { break }
                Start-Sleep -Milliseconds 250
            }
            if ($null -ne (ProcessInfo $p) -or @(Listening 8791).Count -gt 0) {
                throw 'EZS_DEV_STOP_FASTCGI_NOT_EXITED'
            }
        }
        if ($caddyIdentity) {
            # Contrôle d'identité immédiatement avant la terminaison.
            if (-not (OwnedDevCaddy $c)) { throw 'EZS_DEV_STOP_REFUSED_CADDY_IDENTITY_CHANGED' }
            Stop-Process -Id $c -ErrorAction Stop
            for ($attempt=0; $attempt -lt 40; $attempt++) {
                if ($null -eq (ProcessInfo $c) -and @(Listening 8790).Count -eq 0 -and
                    @(Listening 8502).Count -eq 0 -and @(Listening 8852).Count -eq 0) { break }
                Start-Sleep -Milliseconds 250
            }
            if ($null -ne (ProcessInfo $c) -or @(Listening 8790).Count -gt 0 -or
                @(Listening 8502).Count -gt 0 -or @(Listening 8852).Count -gt 0) {
                throw 'EZS_DEV_STOP_CADDY_NOT_EXITED'
            }
        }
        Remove-Item -LiteralPath $stateFile -Force
        Write-Host 'EZS_DEV_ROOT_STOP_OK_8790_8791_8502_8852'
        return
    }
    if ($null -ne $s) {
        $phpId = [int]$s.php_pid
        $caddyId = [int]$s.caddy_pid
        $edgeHealthy = (OwnedDevCaddy $caddyId) -and
            (Port-Owned 8790 $caddyId) -and (Port-Owned 8502 $caddyId) -and
            (Port-Owned 8852 $caddyId)
        if (-not $edgeHealthy) { throw 'EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED' }
        if ($phpId -gt 0 -and (Owned $phpId $php '-b 127.0.0.1:8791') -and (Port-Owned 8791 $phpId)) {
            Write-Host 'EZS_DEV_ALREADY_RUNNING_VERIFIED'
            return
        }
        if ($phpId -ne 0 -or @(Listening 8791).Count -gt 0) {
            throw 'EZS_START_REFUSED_STALE_OR_FOREIGN_ORCHESTRATOR_BACKEND'
        }
        $env:APP_ENV = 'dev'
        $env:APP_DEBUG = '1'
        $env:PHP_FCGI_MAX_REQUESTS = '0'
        $backend = Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:8791' -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if (-not (Wait-Port 8791 ([int]$backend.Id)) -or -not (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791')) {
            if (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791') { Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
            throw 'EZS_START_ORCHESTRATOR_BACKEND_FAILED_SHARED_CADDY_PRESERVED'
        }
        $s.php_pid = [int]$backend.Id
        Save-State $s
        Write-Host 'EZS_START_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED'
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
        if ($null -ne $edge -and (OwnedDevCaddy ([int]$edge.Id))) { Stop-Process -Id $edge.Id -ErrorAction SilentlyContinue }
        if (Owned ([int]$backend.Id) $php '-b 127.0.0.1:8791') { Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
        throw
    }
    Write-Host 'EZS_START_ORCHESTRATOR_CADDY_OK_8790_8791'
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
}
}
function Invoke-EzsLabAssistantLifecycle {
param([ValidateSet('preflight','start','status','stop')][string]$Action='preflight')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$caddy='H:\Caddy\caddy.exe'
$config=Join-Path $root 'config\caddy\Caddyfile.dev-lab-assistant-candidate'
$php='H:\PHP\php-8.5-x64\php-cgi.exe'
$runtime=Join-Path $root 'runtime\v2-dev'
$lockPath=Join-Path $runtime 'lab-assistant.lock'
$statePath=Join-Path $runtime 'lab-assistant.json'
$targets=@(
    @{name='LAB';root='H:\EZStudio_lab';port=8701},
    @{name='ASSISTANT';root='H:\EZStudioLab_assistant';port=8713}
)
function Listener([int]$port){
    return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function Attested([int]$port,[int]$processId,[string]$stamp){
    if($processId -le 0 -or -not $stamp){return $false}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    $l=@(Listener $port)
    if($null -eq $p -or $l.Count -ne 1 -or [int]$l[0].OwningProcess -ne $processId){return $false}
    if(-not [string]::Equals([string]$p.ExecutablePath,$php,[StringComparison]::OrdinalIgnoreCase)){return $false}
    if(-not ([string]$p.CommandLine).Contains("-b 127.0.0.1:$port")){return $false}
    try{return ([datetime]$p.CreationDate).ToUniversalTime().ToString('o') -eq $stamp}catch{return $false}
}
foreach($path in @($php,$caddy,$config)){
    if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "EZS_LA_DEPENDENCY_MISSING:$path"}
}
foreach($target in $targets){
    foreach($relative in @('public\index.php','vendor\autoload_runtime.php')){
        if(-not(Test-Path -LiteralPath (Join-Path $target.root $relative) -PathType Leaf)){
            throw "EZS_LA_DEPENDENCY_MISSING:$($target.name):$relative"
        }
    }
}
& $caddy validate --config $config --adapter caddyfile | Out-Null
if($LASTEXITCODE -ne 0){throw 'EZS_LA_CADDY_CANDIDATE_INVALID'}
if($Action -eq 'preflight'){
    Write-Host 'EZS_LA_PREFLIGHT_OK_CANDIDATE_NOT_APPLIED'
    return
}
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$lock=$null
try{$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_LA_CONCURRENT_OPERATION'}
try{
    if($Action -eq 'stop'){
        if(-not(Test-Path -LiteralPath $statePath)){
            foreach($t in $targets){
                if(@(Listener $t.port).Count -gt 0){throw "EZS_LA_STOP_REFUSED_UNOWNED_PORT_$($t.port)"}
            }
            Write-Host 'EZS_LA_STOP_ALREADY_STOPPED'
            return
        }
        $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if($state.schema -ne 'ezs.la.backends.v1'){throw 'EZS_LA_STOP_REFUSED_INVALID_STATE'}
        foreach($t in $targets){
            $entry=if($t.name -eq 'LAB'){$state.lab}else{$state.assistant}
            if(-not(Attested $t.port ([int]$entry.pid) ([string]$entry.stamp))){
                throw "EZS_LA_STOP_REFUSED_UNVERIFIED_OWNER_$($t.name)"
            }
        }
        foreach($t in $targets){
            $entry=if($t.name -eq 'LAB'){$state.lab}else{$state.assistant}
            Stop-Process -Id ([int]$entry.pid) -ErrorAction Stop
        }
        Remove-Item -LiteralPath $statePath -Force
        Write-Host 'EZS_LA_BACKENDS_STOP_OK_8701_8713_SHARED_CADDY_PRESERVED'
        return
    }
    if(Test-Path -LiteralPath $statePath){
        $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if($state.schema -ne 'ezs.la.backends.v1'){throw 'EZS_LA_STATE_INVALID'}
        foreach($t in $targets){
            $entry=if($t.name -eq 'LAB'){$state.lab}else{$state.assistant}
            if(-not(Attested $t.port ([int]$entry.pid) ([string]$entry.stamp))){
                throw "EZS_LA_STALE_OR_FOREIGN_STATE:$($t.name)"
            }
        }
        Write-Host 'EZS_LA_BACKENDS_ALREADY_RUNNING_VERIFIED'
        return
    }
    if($Action -eq 'status'){
        foreach($t in $targets){Write-Host "EZS_LA_UNMANAGED port=$($t.port) listeners=$(@(Listener $t.port).Count)"}
        return
    }
    foreach($t in $targets){
        if(@(Listener $t.port).Count -gt 0){throw "EZS_LA_REFUSED_UNOWNED_PORT_$($t.port)"}
    }
    $started=@()
    try{
        foreach($t in $targets){
            $env:APP_ENV='dev';$env:APP_DEBUG='1';$env:PHP_FCGI_MAX_REQUESTS='0'
            $p=Start-Process -FilePath $php -ArgumentList "-b 127.0.0.1:$($t.port)" -WorkingDirectory $t.root -WindowStyle Hidden -PassThru
            $started+=@{port=$t.port;pid=[int]$p.Id}
            $ready=$false
            for($i=0;$i -lt 40;$i++){
                $l=@(Listener $t.port)
                if($l.Count -eq 1 -and [int]$l[0].OwningProcess -eq [int]$p.Id){$ready=$true;break}
                if($p.HasExited){break}
                Start-Sleep -Milliseconds 250
            }
            if(-not $ready){throw "EZS_LA_START_FAILED_$($t.port)"}
        }
        $records=@()
        foreach($p in $started){
            $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.pid)"
            if($null -eq $proc){throw 'EZS_LA_START_PROCESS_GONE'}
            $stamp=([datetime]$proc.CreationDate).ToUniversalTime().ToString('o')
            if(-not(Attested $p.port $p.pid $stamp)){throw 'EZS_LA_START_NOT_ATTESTED'}
            $records+=@{pid=$p.pid;stamp=$stamp}
        }
        $state=[ordered]@{schema='ezs.la.backends.v1';lab=$records[0];assistant=$records[1]}
        [IO.File]::WriteAllText($statePath,($state|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_LA_BACKENDS_READY_8701_8713_CADDY_CANDIDATE_STILL_INACTIVE'
    }catch{
        foreach($p in $started){
            $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.pid)" -ErrorAction SilentlyContinue
            if($null -ne $proc -and [string]::Equals([string]$proc.ExecutablePath,$php,[StringComparison]::OrdinalIgnoreCase) -and ([string]$proc.CommandLine).Contains("-b 127.0.0.1:$($p.port)")){
                Stop-Process -Id $p.pid -ErrorAction SilentlyContinue
            }
        }
        throw
    }
}finally{if($null -ne $lock){$lock.Dispose()}}
}

$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$php='H:\PHP\php-8.5-x64\php.exe'
# STOP est exclusivement DEV. PROD est pilotee depuis l'interface.
$runtime=Join-Path $root 'runtime\v2-dev'
$stateFile=Join-Path $runtime 'app-backends.json'
$lockFile=Join-Path $runtime 'app-backends.lock'
$binary='H:\PHP\php-8.5-x64\php-cgi.exe'
function Owned([int]$port,[int]$processId,[string]$stamp){
    if($processId -le 0 -or [string]::IsNullOrWhiteSpace($stamp)){return $false}
    $listeners=@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    if($null -eq $proc -or $listeners.Count -ne 1 -or [int]$listeners[0].OwningProcess -ne $processId){return $false}
    if(-not [string]::Equals([string]$proc.ExecutablePath,$binary,[StringComparison]::OrdinalIgnoreCase) -or
        -not ([string]$proc.CommandLine).Contains("-b 127.0.0.1:$port")){return $false}
    try{return ([datetime]$proc.CreationDate).ToUniversalTime().ToString('o') -eq $stamp}catch{return $false}
}
$lock=$null
try{$lock=[IO.File]::Open($lockFile,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_DEV_APP_CONCURRENT_OPERATION'}
try{
    if(Test-Path -LiteralPath $stateFile){
        $s=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if($s.schema -ne 'ezs.dev.apps.v1' -or -not(Owned 8602 ([int]$s.dev_pid) ([string]$s.dev_created)) -or -not(Owned 8862 ([int]$s.preview_pid) ([string]$s.preview_created))){throw 'EZS_DEV_APP_STOP_REFUSED_UNVERIFIED_OWNERSHIP'}
        Stop-Process -Id ([int]$s.preview_pid) -ErrorAction Stop
        Stop-Process -Id ([int]$s.dev_pid) -ErrorAction Stop
        Remove-Item -LiteralPath $stateFile -Force
        Write-Host 'EZS_DEV_APPS_STOP_OK'
    }elseif(@(Get-NetTCPConnection -LocalPort 8602,8862 -State Listen -ErrorAction SilentlyContinue).Count -gt 0){
        throw 'EZS_DEV_APP_STOP_REFUSED_UNOWNED_LISTENER'
    }
}finally{$lock.Dispose()}
Invoke-EzsLabAssistantLifecycle -Action stop
if(-not $?){throw 'EZS_LA_STOP_FAILED'}
Invoke-EzsRootLifecycle -Action stop
if(-not $?){throw 'EZS_DEV_ROOT_STOP_FAILED'}

# Stop only the AI process recorded and attested by this lifecycle.
function Invoke-EzsAssistantAiLifecycle {
param([ValidateSet('start','stop')][string]$Action)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$assistant='H:\EZStudioLab_assistant'
$exe=Join-Path $assistant 'runtime\ai\bin\llama-server.exe'
$model=Join-Path $assistant 'runtime\models-cache\assistant\bench\qwen2.5-1.5b-instruct-q4_k_m\qwen2.5-1.5b-instruct-q4_k_m.gguf'
$runtime=Join-Path $root 'runtime\v2-dev'
$statePath=Join-Path $runtime 'assistant-ai.json'
$lockPath=Join-Path $runtime 'assistant-ai.lock'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
function Listener {return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8720 -State Listen -ErrorAction SilentlyContinue)}
function Info([int]$processId) {if($processId -le 0){return $null};return Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue}
function Owned($s) {
    if($null -eq $s -or $s.schema -ne 'ezs.assistant.ai.v1' -or [int]$s.pid -le 0 -or -not $s.created){return $false}
    $p=Info ([int]$s.pid)
    $ports=@(Listener)
    if($null -eq $p -or $ports.Count -ne 1 -or [int]$ports[0].OwningProcess -ne [int]$s.pid){return $false}
    if(-not [string]::Equals([string]$p.ExecutablePath,$exe,[StringComparison]::OrdinalIgnoreCase)){return $false}
    $cmd=[string]$p.CommandLine
    if(-not $cmd.Contains($model) -or $cmd -notmatch '(?i)(?:^|\s)--port\s+8720(?:\s|$)'){return $false}
    try{return ([datetime]$p.CreationDate).ToUniversalTime().ToString('o') -eq [string]$s.created}catch{return $false}
}
function Health {
    try{$r=Invoke-RestMethod 'http://127.0.0.1:8720/health' -TimeoutSec 2 -ErrorAction Stop;return $r.status -eq 'ok'}catch{return $false}
}
$lock=$null
try{$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_AI_CONCURRENT_OPERATION'}
try {
    $s=$null
    if(Test-Path -LiteralPath $statePath -PathType Leaf){
        try{$s=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json}catch{throw 'EZS_AI_INVALID_STATE'}
    }
    if($Action -eq 'stop'){
        if($null -eq $s){Write-Host 'EZS_AI_STOP_UNMANAGED_PRESERVED';return}
        if(-not(Owned $s)){throw 'EZS_AI_STOP_REFUSED_UNVERIFIED_PROCESS'}
        Stop-Process -Id ([int]$s.pid) -ErrorAction Stop
        for($i=0;$i -lt 40;$i++){
            if($null -eq (Info ([int]$s.pid)) -and @(Listener).Count -eq 0){break}
            Start-Sleep -Milliseconds 250
        }
        if($null -ne (Info ([int]$s.pid)) -or @(Listener).Count -gt 0){throw 'EZS_AI_STOP_INCOMPLETE'}
        Remove-Item -LiteralPath $statePath -Force
        Write-Host 'EZS_AI_STOP_OWNED_OK'
        return
    }
    if($null -ne $s){
        if(-not(Owned $s) -or -not(Health)){throw 'EZS_AI_START_REFUSED_STALE_OR_UNHEALTHY_OWNED_STATE'}
        Write-Host 'EZS_AI_ALREADY_RUNNING_VERIFIED'
        return
    }
    if(@(Listener).Count -gt 0){Write-Host 'EZS_AI_EXISTING_UNMANAGED_LISTENER_PRESERVED';return}
    foreach($path in @($exe,$model)){if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "EZS_AI_DEPENDENCY_MISSING:$path"}}
    # CPU conservative profile as qualified in 4.2c15. No model download.
    $args=@('-m',('"'+$model+'"'),'--host','127.0.0.1','--port','8720','--ctx-size','4096','--parallel','1','--gpu-layers','0')
    $p=Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $assistant -WindowStyle Hidden -PassThru
    $record=$null
    try {
        for($i=0;$i -lt 240;$i++){
            if($p.HasExited){throw 'EZS_AI_PROCESS_EXITED_BEFORE_READY'}
            $proc=Info ([int]$p.Id)
            if($null -ne $proc -and @(Listener).Count -eq 1 -and [int](Listener)[0].OwningProcess -eq [int]$p.Id -and (Health)){
                $record=[pscustomobject]@{schema='ezs.assistant.ai.v1';pid=[int]$p.Id;created=([datetime]$proc.CreationDate).ToUniversalTime().ToString('o')}
                if(Owned $record){break}
            }
            Start-Sleep -Milliseconds 500
        }
        if($null -eq $record -or -not(Owned $record)){throw 'EZS_AI_READY_TIMEOUT_OR_IDENTITY_FAILURE'}
        [IO.File]::WriteAllText($statePath,($record|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_AI_START_OWNED_READY_8720'
    }catch{
        $proc=Info ([int]$p.Id)
        if($null -ne $proc -and [string]::Equals([string]$proc.ExecutablePath,$exe,[StringComparison]::OrdinalIgnoreCase) -and
            ([string]$proc.CommandLine).Contains($model)){Stop-Process -Id ([int]$p.Id) -ErrorAction SilentlyContinue}
        throw
    }
}finally{if($null -ne $lock){$lock.Dispose()}}
}

Invoke-EzsAssistantAiLifecycle -Action stop
