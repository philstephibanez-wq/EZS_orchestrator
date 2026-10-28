$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime=Join-Path $root 'runtime\v2-dev'
$stateFile=Join-Path $runtime 'app-backends.json'
$lockFile=Join-Path $runtime 'app-backends.lock'
$binary='H:\PHP\php-8.5-x64\php-cgi.exe'
$app='H:\EZScore_dev'
function Owners([int]$port){return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)}
function IsOwned([int]$port,[int]$processId,[string]$stamp){
    if($processId -le 0 -or [string]::IsNullOrWhiteSpace($stamp)){return $false}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    $listeners=@(Owners $port)
    if($null -eq $p -or $listeners.Count -ne 1 -or [int]$listeners[0].OwningProcess -ne $processId){return $false}
    if(-not [string]::Equals([string]$p.ExecutablePath,$binary,[StringComparison]::OrdinalIgnoreCase)){return $false}
    if(-not ([string]$p.CommandLine).Contains("-b 127.0.0.1:$port")){return $false}
    try {return ([datetime]$p.CreationDate).ToUniversalTime().ToString('o') -eq $stamp} catch{return $false}
}
function WaitOwned([int]$port,[int]$pid){
    for($i=0;$i -lt 40;$i++){
        $listeners=@(Owners $port)
        if($listeners.Count -eq 1 -and [int]$listeners[0].OwningProcess -eq $pid){return $true}
        Start-Sleep -Milliseconds 250
    }
    return $false
}
function HttpReady([int]$port,[string]$path){
    try {
        $request=[System.Net.HttpWebRequest]::Create("http://127.0.0.1:$port$path")
        $request.Timeout=5000
        $request.AllowAutoRedirect=$false
        $response=$request.GetResponse()
        $code=[int]$response.StatusCode
        $response.Close()
        return ($code -ge 200 -and $code -lt 400)
    } catch [System.Net.WebException] {
        $response=$_.Exception.Response
        if($null -ne $response){$code=[int]$response.StatusCode;$response.Close();return ($code -eq 401 -or $code -eq 403)}
        return $false
    }
}
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action start
if(-not $?){throw 'EZS_DEV_ROOT_START_FAILED'}
if(-not(Test-Path -LiteralPath $app\public\index.php -PathType Leaf)){throw 'EZS_DEV_APP_INDEX_MISSING'}
if(-not(Test-Path -LiteralPath $binary -PathType Leaf)){throw 'EZS_DEV_APP_PHP_CGI_MISSING'}
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$lock=$null
try {$lock=[IO.File]::Open($lockFile,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_DEV_APP_CONCURRENT_OPERATION'}
try{
    if(Test-Path -LiteralPath $stateFile){
        $s=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if($s.schema -ne 'ezs.dev.apps.v1' -or -not(IsOwned 8602 ([int]$s.dev_pid) ([string]$s.dev_created)) -or
           -not(IsOwned 8862 ([int]$s.preview_pid) ([string]$s.preview_created))){
            throw 'EZS_DEV_APP_REFUSED_STALE_STATE'
        }
        if(-not(HttpReady 8502 '/fr/login') -or -not(HttpReady 8852 '/fr/login')){throw 'EZS_DEV_APP_HTTP_UNHEALTHY'}
        Write-Host 'EZS_DEV_APPS_ALREADY_RUNNING_VERIFIED'
        return
    }
    foreach($port in @(8602,8862)){if(@(Owners $port).Count -gt 0){throw "EZS_DEV_APP_REFUSED_FOREIGN_LISTENER_$port"}}
    $env:APP_ENV='dev';$env:APP_DEBUG='1';$env:PHP_FCGI_MAX_REQUESTS='0'
    Remove-Item Env:EZS_GATEWAY_RECIPE_CONFIG -ErrorAction SilentlyContinue
    Remove-Item Env:EZS_GATEWAY_RECIPE_MODE -ErrorAction SilentlyContinue
    $started=@()
    try{
        foreach($port in @(8602,8862)){
            $p=Start-Process -FilePath $binary -ArgumentList "-b 127.0.0.1:$port" -WorkingDirectory $app -WindowStyle Hidden -PassThru
            $started+=@{pid=[int]$p.Id;port=$port}
            if(-not(WaitOwned $port ([int]$p.Id))){throw "EZS_DEV_APP_FASTCGI_START_FAILED_$port"}
        }
        $dev=Get-CimInstance Win32_Process -Filter "ProcessId=$($started[0].pid)"
        $preview=Get-CimInstance Win32_Process -Filter "ProcessId=$($started[1].pid)"
        if($null -eq $dev -or $null -eq $preview){throw 'EZS_DEV_APP_IDENTITY_UNAVAILABLE'}
        $state=[ordered]@{schema='ezs.dev.apps.v1';dev_pid=$started[0].pid;dev_created=([datetime]$dev.CreationDate).ToUniversalTime().ToString('o');preview_pid=$started[1].pid;preview_created=([datetime]$preview.CreationDate).ToUniversalTime().ToString('o')}
        if(-not(IsOwned 8602 $state.dev_pid $state.dev_created) -or -not(IsOwned 8862 $state.preview_pid $state.preview_created)){throw 'EZS_DEV_APP_OWNERSHIP_NOT_CONFIRMED'}
        if(-not(HttpReady 8502 '/fr/login') -or -not(HttpReady 8852 '/fr/login')){throw 'EZS_DEV_APP_HTTP_NOT_READY'}
        [IO.File]::WriteAllText($stateFile,($state|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_DEV_APPS_READY_8502_8852'
    }catch{
        foreach($entry in $started){
            $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($entry.pid)" -ErrorAction SilentlyContinue
            if($null -ne $proc -and [string]::Equals([string]$proc.ExecutablePath,$binary,[StringComparison]::OrdinalIgnoreCase) -and ([string]$proc.CommandLine).Contains("-b 127.0.0.1:$($entry.port)")){
                Stop-Process -Id $entry.pid -ErrorAction SilentlyContinue
            }
        }
        throw
    }
}finally{$lock.Dispose()}
