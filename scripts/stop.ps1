param([ValidateSet('all','dev','gateway')][string]$Target='all')
$ErrorActionPreference='Stop'
if($Target -eq 'all') {
    $root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $gatewayState=Join-Path $root 'runtime\v2-prod\gateway-php.json'
    if(Test-Path -LiteralPath $gatewayState) {
        & (Join-Path $PSScriptRoot 'stop.ps1') -Target gateway
        if(-not $?) {throw 'EZS_GLOBAL_STOP_GATEWAY_FAILED'}
    } elseif(@(Get-NetTCPConnection -LocalPort 8510 -State Listen -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'EZS_GLOBAL_STOP_REFUSED_UNOWNED_GATEWAY'
    }
    $devState=Join-Path $root 'runtime\v2-dev\processes.json'
    if(Test-Path -LiteralPath $devState) {
        & (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
        if(-not $?) {throw 'EZS_GLOBAL_STOP_DEV_FAILED'}
    }
    Write-Host 'EZS_GLOBAL_STOP_OWNED_COMPONENTS_OK'
    return
}
if($Target -eq 'dev') {
    & (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
    exit $LASTEXITCODE
}
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime=Join-Path $root 'runtime\v2-prod'
$stateFile=Join-Path $runtime 'gateway-php.json'
$lockFile=Join-Path $runtime 'gateway-php.lock'
$php='H:\PHP\php-8.5-x64\php-cgi.exe'
$caddy='H:\Caddy\caddy.exe'
function Owned([int]$id,[int]$port,[string]$exe,[string]$signature){
    if($id -le 0){return $false}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    $listeners=@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    return ($null -ne $p -and [string]::Equals([string]$p.ExecutablePath,$exe,[StringComparison]::OrdinalIgnoreCase) -and
        ([string]$p.CommandLine).Contains($signature) -and -not [string]::IsNullOrEmpty([string]$p.CreationDate) -and
        $listeners.Count -eq 1 -and [int]$listeners[0].OwningProcess -eq $id)
}
$mutex=$null
try{$mutex=[IO.File]::Open($lockFile,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_GATEWAY_PHP_CONCURRENT_OPERATION'}
try{
    if(-not(Test-Path -LiteralPath $stateFile)){Write-Host 'EZS_GATEWAY_PHP_NOT_OWNED';return}
    $s=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if($s.schema -ne 'ezs.gateway.php.runtime.v1' -or
        -not(Owned ([int]$s.caddy_pid) 8510 $caddy 'Caddyfile.gateway-php-prod') -or
        -not(Owned ([int]$s.php_pid) 18515 $php '-b 127.0.0.1:18515')){
        throw 'EZS_GATEWAY_PHP_STOP_REFUSED_UNVERIFIED_IDENTITY'
    }
    Stop-Process -Id ([int]$s.caddy_pid) -ErrorAction Stop
    Stop-Process -Id ([int]$s.php_pid) -ErrorAction Stop
    Remove-Item -LiteralPath $stateFile -Force
    Write-Host 'EZS_GATEWAY_PHP_STOP_OWNED_ONLY_OK'
}finally{$mutex.Dispose()}
