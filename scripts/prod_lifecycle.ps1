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
