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
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
if(-not $?){throw 'EZS_DEV_ROOT_STOP_FAILED_PROD_MAINTENANCE_PRESERVED'}
