param([ValidateSet('all','dev','gateway')][string]$Target='all')
$ErrorActionPreference='Stop'
if($Target -eq 'all') {
    $devState=Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'runtime\v2-dev\processes.json'
    $devStatus=(& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action status 6>&1 | Out-String)
    if($devStatus -match 'php_owned=True caddy_owned=True state_present=True') {
        Write-Host 'EZS_GLOBAL_START_DEV_ALREADY_READY'
    } elseif(-not (Test-Path -LiteralPath $devState)) {
        & (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action start
        if(-not $?) {throw 'EZS_GLOBAL_START_DEV_FAILED'}
    } else {
        throw 'EZS_GLOBAL_START_REFUSED_DEV_STALE_OR_PARTIAL_STATE'
    }
    $root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $phpState=Join-Path $root 'runtime\v2-prod\gateway-php.json'
    if(Test-Path -LiteralPath $phpState) {
        $s=Get-Content -LiteralPath $phpState -Raw -Encoding UTF8 | ConvertFrom-Json
        $listeners=@(Get-NetTCPConnection -LocalPort 8510 -State Listen -ErrorAction SilentlyContinue)
        $backend=@(Get-NetTCPConnection -LocalPort 18515 -State Listen -ErrorAction SilentlyContinue)
        if($s.schema -ne 'ezs.gateway.php.runtime.v1' -or
           $listeners.Count -ne 1 -or [int]$listeners[0].OwningProcess -ne [int]$s.caddy_pid -or
           $backend.Count -ne 1 -or [int]$backend[0].OwningProcess -ne [int]$s.php_pid) {
            throw 'EZS_GLOBAL_START_REFUSED_GATEWAY_STALE_STATE'
        }
        $res=Invoke-WebRequest 'http://127.0.0.1:8510/__ezscore_gateway_status' -UseBasicParsing -TimeoutSec 5
        $payload=$res.Content | ConvertFrom-Json
        if($payload.protocol -ne 'ezscore.online-gateway.v3') {throw 'EZS_GLOBAL_START_GATEWAY_PROTOCOL_INVALID'}
        Write-Host 'EZS_GLOBAL_START_GATEWAY_ALREADY_READY'
    } else {
        & (Join-Path $PSScriptRoot 'start.ps1') -Target gateway
        if(-not $?) {throw 'EZS_GLOBAL_START_GATEWAY_FAILED'}
    }
    Write-Host 'EZS_GLOBAL_START_READY'
    return
}
if($Target -eq 'dev') {
    & (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action start
    exit $LASTEXITCODE
}
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime=Join-Path $root 'runtime\v2-prod'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$lockFile=Join-Path $runtime 'gateway-php.lock'
$stateFile=Join-Path $runtime 'gateway-php.json'
$php='H:\PHP\php-8.5-x64\php-cgi.exe'
$caddy='H:\Caddy\caddy.exe'
$config=Join-Path $root 'config\caddy\Caddyfile.gateway-php-prod'
$mutex=$null
function Listener([int]$port) {
    return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function Identity([int]$id,[string]$exe,[string]$signature) {
    if($id -le 0) {return $false}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    return ($null -ne $p -and
        [string]::Equals([string]$p.ExecutablePath,$exe,[StringComparison]::OrdinalIgnoreCase) -and
        ([string]$p.CommandLine).Contains($signature) -and
        -not [string]::IsNullOrEmpty([string]$p.CreationDate))
}
function WaitOwned([int]$port,[int]$id,[string]$exe,[string]$sig) {
    for($i=0;$i -lt 40;$i++){
        $listeners=@(Listener $port)
        if($listeners.Count -eq 1 -and [int]$listeners[0].OwningProcess -eq $id -and (Identity $id $exe $sig)){return $true}
        if(-not (Identity $id $exe $sig)){return $false}
        Start-Sleep -Milliseconds 250
    }
    return $false
}
try {
    $mutex=[IO.File]::Open($lockFile,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
} catch {throw 'EZS_GATEWAY_PHP_CONCURRENT_OPERATION'}
try {
    if(Test-Path -LiteralPath $stateFile){throw 'EZS_GATEWAY_PHP_REFUSED_EXISTING_STATE'}
    foreach($port in @(8510,18515)){
        if(@(Listener $port).Count -gt 0){throw "EZS_GATEWAY_PHP_REFUSED_PORT_OCCUPIED_$port"}
    }
    foreach($path in @($php,$caddy,$config,(Join-Path $root 'runtime_components\prod_gateway_php\router.php'),'H:\EZScore\var\runtime\online-gateway.json')){
        if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "EZS_GATEWAY_PHP_MISSING:$path"}
    }
    & $caddy validate --config $config --adapter caddyfile | Out-Null
    if($LASTEXITCODE -ne 0){throw 'EZS_GATEWAY_PHP_CADDY_INVALID'}
    # A recipe may have exported test overrides into the parent user environment.
    # Production gateway MUST inherit no recipe variables.
    Remove-Item Env:EZS_GATEWAY_RECIPE_CONFIG -ErrorAction SilentlyContinue
    Remove-Item Env:EZS_GATEWAY_RECIPE_MODE -ErrorAction SilentlyContinue
    $env:APP_ENV='prod';$env:APP_DEBUG='0';$env:PHP_FCGI_MAX_REQUESTS='0'
    $cgi=$null;$edge=$null
    try {
        $cgi=Start-Process -FilePath $php -ArgumentList '-b 127.0.0.1:18515' -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if(-not(WaitOwned 18515 ([int]$cgi.Id) $php '-b 127.0.0.1:18515')){throw 'EZS_GATEWAY_PHP_FASTCGI_NOT_READY'}
        $edge=Start-Process -FilePath $caddy -ArgumentList @('run','--config',('"' + $config + '"'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if(-not(WaitOwned 8510 ([int]$edge.Id) $caddy 'Caddyfile.gateway-php-prod')){throw 'EZS_GATEWAY_PHP_CADDY_NOT_READY'}
        $res=Invoke-WebRequest 'http://127.0.0.1:8510/__ezscore_gateway_status' -UseBasicParsing -TimeoutSec 5
        $payload=$res.Content | ConvertFrom-Json
        if([int]$res.StatusCode -ne 200 -or $payload.protocol -ne 'ezscore.online-gateway.v3' -or $payload.backend_port -ne 8511){
            throw 'EZS_GATEWAY_PHP_PROTOCOL_INVALID'
        }
        $state=[ordered]@{
            schema='ezs.gateway.php.runtime.v1'
            caddy_pid=[int]$edge.Id
            php_pid=[int]$cgi.Id
            started_utc=[DateTime]::UtcNow.ToString('o')
        }
        [IO.File]::WriteAllText($stateFile,($state|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_GATEWAY_PHP_PROD_8510_READY'
    } catch {
        if($edge -and (Identity ([int]$edge.Id) $caddy 'Caddyfile.gateway-php-prod')){Stop-Process -Id $edge.Id -ErrorAction SilentlyContinue}
        if($cgi -and (Identity ([int]$cgi.Id) $php '-b 127.0.0.1:18515')){Stop-Process -Id $cgi.Id -ErrorAction SilentlyContinue}
        throw
    }
} finally {$mutex.Dispose()}
