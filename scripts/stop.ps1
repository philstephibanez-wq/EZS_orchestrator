param([ValidateSet('stop','status','maintenance')][string]$ProdAction='')

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
        if ($null -eq $s) { throw 'EZS_STOP_REFUSED_NO_OWNED_STATE_SHARED_CADDY_PRESERVED' }
        $p = [int]$s.php_pid
        $c = [int]$s.caddy_pid
        if (-not (OwnedDevCaddy $c) -or -not (Port-Owned 8790 $c) -or
            -not (Port-Owned 8502 $c) -or -not (Port-Owned 8852 $c)) {
            throw 'EZS_STOP_REFUSED_UNVERIFIED_SHARED_CADDY'
        }
        if ($p -eq 0 -and @(Listening 8791).Count -eq 0) {
            Write-Host 'EZS_STOP_ORCHESTRATOR_ALREADY_STOPPED_SHARED_CADDY_PRESERVED'
            return
        }
        if (-not (Owned $p $php '-b 127.0.0.1:8791') -or -not (Port-Owned 8791 $p)) {
            throw 'EZS_STOP_REFUSED_UNVERIFIED_ORCHESTRATOR_BACKEND'
        }
        Stop-Process -Id $p -ErrorAction Stop
        $s.php_pid = 0
        Save-State $s
        Write-Host 'EZS_STOP_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED'
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
if($ProdAction -ne ''){Invoke-EzsProdLifecycle -Action $ProdAction;return}
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
function Invoke-EzsProdLifecycle {
param([ValidateSet('start','stop','status','normal','maintenance','repair-fastcgi')][string]$Action='status')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime=Join-Path $root 'runtime\v2-prod'
$statePath=Join-Path $runtime 'processes.json'
$lockPath=Join-Path $runtime 'lifecycle.lock'
$php='H:\PHP\php-8.5-x64\php-cgi.exe'
$caddy='H:\Caddy\caddy.exe'
$python='H:\Python\pythoncore-3.14-64\python.exe'
$prod='H:\EZScore'
$configPath=Join-Path $prod 'var\runtime\online-gateway.json'
$internal=Join-Path $root 'config\caddy\Caddyfile.prod-internal-candidate'
$edge=Join-Path $root 'config\caddy\Caddyfile.prod'
$gateway=Join-Path $root 'runtime_components\prod_gateway\server.py'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
function Listener([int]$port) { return @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }
function Info([int]$processId) { if($processId -le 0){return $null};return Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue }
function Own([int]$processId,[string]$binary,[string]$signature) {
    $p=Info $processId
    return ($null -ne $p -and [string]::Equals([string]$p.ExecutablePath,$binary,[StringComparison]::OrdinalIgnoreCase) -and ([string]$p.CommandLine).Contains($signature))
}
function OwnPort([int]$port,[int]$processId) { $l=@(Listener $port);return ($l.Count -eq 1 -and [int]$l[0].OwningProcess -eq $processId) }
function AwaitPort([int]$port,[int]$processId) {
    for($i=0;$i -lt 40;$i++){if(OwnPort $port $processId){return $true};if($null -eq (Info $processId)){return $false};Start-Sleep -Milliseconds 250}
    return (OwnPort $port $processId)
}
function State { if(-not (Test-Path -LiteralPath $statePath)){return $null};return (Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json) }
function WriteUtf8([string]$path,[string]$value){[IO.File]::WriteAllText($path,$value,[Text.UTF8Encoding]::new($false))}
function SetMode([bool]$maintenance) {
    $payload=[ordered]@{schema_version='ezscore.online-gateway.v1';maintenance=$maintenance;backend_host='127.0.0.1';backend_port=8511;public_url='http://127.0.0.1:8501'}
    $temp=$configPath+'.ezs-tmp'
    WriteUtf8 $temp ($payload | ConvertTo-Json)
    Move-Item -LiteralPath $temp -Destination $configPath -Force
}
function Ready($s) {
    return ((Own ([int]$s.php_pid) $php '-b 127.0.0.1:8512') -and (OwnPort 8512 ([int]$s.php_pid)) -and
        (Own ([int]$s.internal_pid) $caddy 'Caddyfile.prod-internal-candidate') -and (OwnPort 8511 ([int]$s.internal_pid)) -and
        (Own ([int]$s.gateway_pid) $python 'runtime_components\prod_gateway\server.py') -and (OwnPort 8510 ([int]$s.gateway_pid)) -and
        (Own ([int]$s.edge_pid) $caddy 'Caddyfile.prod') -and (OwnPort 8501 ([int]$s.edge_pid)))
}
function Http([string]$url) {
    try { $response=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop;return [int]$response.StatusCode }
    catch { if($_.Exception.Response){return [int]$_.Exception.Response.StatusCode};return 0 }
}
function WaitExit([int]$processId,[int]$port) {
    for($i=0;$i -lt 40;$i++){if($null -eq (Info $processId) -and @(Listener $port).Count -eq 0){return $true};Start-Sleep -Milliseconds 250}
    return $false
}
$lock=$null
try {$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)} catch {throw 'EZS_PROD_CONCURRENT_OPERATION'}
try {
    $s=State
    if($Action -eq 'status'){
        $ready=$false
        if($null -ne $s){$ready=Ready $s}
        Write-Host "EZS_PROD_STATUS ready=$ready state_present=$($null -ne $s)"
        return
    }
    if($Action -eq 'repair-fastcgi'){
        if($null -eq $s){throw 'EZS_PROD_FASTCGI_REPAIR_REFUSED_NO_STATE'}
        $oldPid=[int]$s.php_pid
        if(-not (Own ([int]$s.internal_pid) $caddy 'Caddyfile.prod-internal-candidate') -or -not (OwnPort 8511 ([int]$s.internal_pid)) -or
           -not (Own ([int]$s.gateway_pid) $python 'runtime_components\prod_gateway\server.py') -or -not (OwnPort 8510 ([int]$s.gateway_pid)) -or
           -not (Own ([int]$s.edge_pid) $caddy 'Caddyfile.prod') -or -not (OwnPort 8501 ([int]$s.edge_pid))) {
            throw 'EZS_PROD_FASTCGI_REPAIR_REFUSED_OTHER_COMPONENTS_UNVERIFIED'
        }
        if((Own $oldPid $php '-b 127.0.0.1:8512') -and (OwnPort 8512 $oldPid)){
            Write-Host 'EZS_PROD_FASTCGI_REPAIR_NOT_NEEDED';return
        }
        if(@(Listener 8512).Count -gt 0 -or $null -ne (Info $oldPid)){
            throw 'EZS_PROD_FASTCGI_REPAIR_REFUSED_PROCESS_OR_PORT_PRESENT'
        }
        if(-not (Test-Path -LiteralPath $php -PathType Leaf)){throw 'EZS_PROD_FASTCGI_REPAIR_MISSING_BINARY'}
        $env:APP_ENV='prod';$env:APP_DEBUG='0'
        $env:PHP_FCGI_MAX_REQUESTS='0'
        $p=Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:8512' -WorkingDirectory $prod -WindowStyle Hidden -PassThru
        if(-not (AwaitPort 8512 ([int]$p.Id)) -or -not (Own ([int]$p.Id) $php '-b 127.0.0.1:8512')){
            if(Own ([int]$p.Id) $php '-b 127.0.0.1:8512'){Stop-Process -Id $p.Id -ErrorAction SilentlyContinue}
            throw 'EZS_PROD_FASTCGI_REPAIR_FAILED'
        }
        $s.php_pid=[int]$p.Id
        WriteUtf8 $statePath ($s | ConvertTo-Json)
        Write-Host 'EZS_PROD_FASTCGI_REPAIR_OK_OTHER_COMPONENTS_PRESERVED'
        return
    }
    if($Action -eq 'start'){
        if($null -ne $s){throw 'EZS_PROD_REFUSED_EXISTING_STATE'}
        foreach($port in @(8501,8510,8511,8512,2020,2022)){if(@(Listener $port).Count -gt 0){throw "EZS_PROD_REFUSED_OCCUPIED_$port"}}
        foreach($path in @($php,$caddy,$python,$internal,$edge,$gateway,(Join-Path $prod 'public\index.php'))){if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "EZS_PROD_MISSING:$path"}}
        if(-not (Test-Path (Split-Path $configPath) -PathType Container)){throw 'EZS_PROD_GATEWAY_RUNTIME_MISSING'}
        & $caddy validate --config $internal --adapter caddyfile | Out-Null
        if($LASTEXITCODE -ne 0){throw 'EZS_PROD_INTERNAL_CONFIG_INVALID'}
        & $caddy validate --config $edge --adapter caddyfile | Out-Null
        if($LASTEXITCODE -ne 0){throw 'EZS_PROD_EDGE_CONFIG_INVALID'}
        $env:APP_ENV='prod';$env:APP_DEBUG='0'
        $env:PHP_FCGI_MAX_REQUESTS='0'
        $started=@()
        try {
            $p=Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:8512' -WorkingDirectory $prod -WindowStyle Hidden -PassThru
            $started+=@{id=[int]$p.Id;exe=$php;sig='-b 127.0.0.1:8512'}
            if(-not (AwaitPort 8512 ([int]$p.Id))){throw 'EZS_PROD_FASTCGI_FAILED'}
            $i=Start-Process -FilePath $caddy -ArgumentList @('run','--config',('"' + $internal + '"'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -PassThru
            $started+=@{id=[int]$i.Id;exe=$caddy;sig='Caddyfile.prod-internal-candidate'}
            if(-not (AwaitPort 8511 ([int]$i.Id))){throw 'EZS_PROD_INTERNAL_FAILED'}
            SetMode $true
            $g=Start-Process -FilePath $python -ArgumentList @('-u',('"' + $gateway + '"'),'--root',('"' + $prod + '"'),'--host','127.0.0.1','--port','8510') -WorkingDirectory $root -WindowStyle Hidden -PassThru
            $started+=@{id=[int]$g.Id;exe=$python;sig='runtime_components\prod_gateway\server.py'}
            if(-not (AwaitPort 8510 ([int]$g.Id))){throw 'EZS_PROD_GATEWAY_FAILED'}
            if((Http 'http://127.0.0.1:8510/__ezscore_gateway_status') -ne 200){throw 'EZS_PROD_GATEWAY_PROTOCOL_FAILED'}
            $e=Start-Process -FilePath $caddy -ArgumentList @('run','--config',('"' + $edge + '"'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -PassThru
            $started+=@{id=[int]$e.Id;exe=$caddy;sig='Caddyfile.prod'}
            if(-not (AwaitPort 8501 ([int]$e.Id))){throw 'EZS_PROD_EDGE_FAILED'}
            WriteUtf8 $statePath (([ordered]@{php_pid=[int]$p.Id;internal_pid=[int]$i.Id;gateway_pid=[int]$g.Id;edge_pid=[int]$e.Id}) | ConvertTo-Json)
            Write-Host 'EZS_PROD_START_MAINTENANCE_OK'
        }catch{
            $failure=$_
            [array]::Reverse($started)
            foreach($proc in $started){if(Own $proc.id $proc.exe $proc.sig){Stop-Process -Id $proc.id -ErrorAction SilentlyContinue}}
            throw $failure
        }
        return
    }
    if($null -eq $s -or -not (Ready $s)){throw 'EZS_PROD_REFUSED_UNVERIFIED_PROCESS_OWNERSHIP'}
    if($Action -eq 'maintenance'){
        SetMode $true
        if((Http 'http://127.0.0.1:8501/') -ne 503){throw 'EZS_PROD_MAINTENANCE_UNCONFIRMED'}
        Write-Host 'EZS_PROD_MAINTENANCE_OK';return
    }
    if($Action -eq 'normal'){
        SetMode $true
        $code=Http 'http://127.0.0.1:8511/'
        if($code -lt 200 -or $code -ge 500){throw "EZS_PROD_NORMAL_REFUSED_BACKEND_$code"}
        SetMode $false
        Write-Host 'EZS_PROD_NORMAL_REQUESTED_VERIFY_SSO_MEDIA';return
    }
    if($Action -eq 'stop'){
        SetMode $true
        if((Http 'http://127.0.0.1:8501/') -ne 503){throw 'EZS_PROD_STOP_REFUSED_MAINTENANCE_UNCONFIRMED'}
        foreach($proc in @(@{id=[int]$s.edge_pid;port=8501},@{id=[int]$s.gateway_pid;port=8510},@{id=[int]$s.internal_pid;port=8511},@{id=[int]$s.php_pid;port=8512})){
            Stop-Process -Id $proc.id -ErrorAction Stop
            if(-not (WaitExit $proc.id $proc.port)){throw 'EZS_PROD_STOP_INCOMPLETE_STATE_PRESERVED'}
        }
        Remove-Item -LiteralPath $statePath -Force
        Write-Host 'EZS_PROD_STOP_VERIFIED_DEV_UNTOUCHED'
    }
} finally {if($null -ne $lock){$lock.Dispose()}}
}

$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$php='H:\PHP\php-8.5-x64\php.exe'
$entry=Join-Path $root 'bin\prod_mode.php'
if(-not(Test-Path -LiteralPath $php -PathType Leaf) -or -not(Test-Path -LiteralPath $entry -PathType Leaf)){throw 'EZS_STOP_MAINTENANCE_DEPENDENCY_MISSING'}
& $php $entry maintenance
if($LASTEXITCODE -ne 0){throw 'EZS_STOP_REFUSED_PROD_MAINTENANCE_UNCONFIRMED'}
Write-Host 'EZS_STOP_PROD_MAINTENANCE_CONFIRMED'
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
if(-not $?){throw 'EZS_LA_STOP_FAILED_SHARED_CADDY_PRESERVED'}
Invoke-EzsRootLifecycle -Action stop
if(-not $?){throw 'EZS_DEV_ROOT_STOP_FAILED_PROD_MAINTENANCE_PRESERVED'}

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
