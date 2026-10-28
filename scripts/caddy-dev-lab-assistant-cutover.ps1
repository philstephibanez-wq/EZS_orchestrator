param([ValidateSet('preflight','apply','status')][string]$Action='preflight')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime=Join-Path $root 'runtime\v2-dev'
$statePath=Join-Path $runtime 'processes.json'
$lockPath=Join-Path $runtime 'lifecycle.lock'
$caddy='H:\Caddy\caddy.exe'
$oldConfig=Join-Path $root 'config\caddy\Caddyfile.dev-root-candidate'
$newConfig=Join-Path $root 'config\caddy\Caddyfile.dev-lab-assistant-candidate'
$requiredPorts=@(8790,8502,8852)
$allPorts=@(8790,8502,8852,8702,8712)
function Listener([int]$port) {
    return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function Proc([int]$processId) {
    return Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
}
function Owned([int]$processId,[string]$configName,[string]$stamp) {
    $p=Proc $processId
    if($null -eq $p -or -not [string]::Equals([string]$p.ExecutablePath,$caddy,[StringComparison]::OrdinalIgnoreCase) -or
       -not ([string]$p.CommandLine).Contains($configName)) {return $false}
    if($stamp) {
        try { if(([datetime]$p.CreationDate).ToUniversalTime().ToString('o') -ne $stamp) {return $false} }
        catch {return $false}
    }
    return $true
}
function WaitPorts([int]$processId,[int[]]$ports,[int]$seconds=20) {
    $end=[DateTime]::UtcNow.AddSeconds($seconds)
    do {
        $ok=$true
        foreach($port in $ports) {
            $l=@(Listener $port)
            if($l.Count -ne 1 -or [int]$l[0].OwningProcess -ne $processId) {$ok=$false}
        }
        if($ok) {return $true}
        if($null -eq (Proc $processId)) {return $false}
        Start-Sleep -Milliseconds 250
    }while([DateTime]::UtcNow -lt $end)
    return $false
}
function HttpCode([int]$port,[string]$path) {
    try{
        $r=[Net.HttpWebRequest]::Create("http://127.0.0.1:$port$path")
        $r.Timeout=6000;$r.AllowAutoRedirect=$false
        $response=$r.GetResponse()
        $code=[int]$response.StatusCode;$response.Close()
        return $code
    }catch [Net.WebException] {
        if($null -ne $_.Exception.Response){
            $response=$_.Exception.Response
            $code=[int]$response.StatusCode;$response.Close()
            return $code
        }
        return 0
    }
}
function CheckHttp([int[]]$ports) {
    foreach($port in $ports) {
        $path=if($port -eq 8502 -or $port -eq 8852) {'/fr/login'}else{'/'}
        $code=HttpCode $port $path
        Write-Host "EZS_CADDY_HTTP port=$port status=$code"
        if($code -lt 200 -or $code -ge 500) {return $false}
    }
    return $true
}
foreach($path in @($caddy,$oldConfig,$newConfig,$statePath)) {
    if(-not(Test-Path -LiteralPath $path -PathType Leaf)) {throw "EZS_CADDY_MISSING:$path"}
}
& $caddy validate --config $newConfig --adapter caddyfile | Out-Null
if($LASTEXITCODE -ne 0){throw 'EZS_CADDY_CANDIDATE_INVALID'}
if($Action -eq 'preflight') {
    Write-Host 'EZS_CADDY_CUTOVER_PREFLIGHT_OK_NO_MUTATION'
    return
}
$lock=$null
try{$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_CADDY_CUTOVER_CONCURRENT_OPERATION'}
try {
    $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $oldPid=[int]$state.caddy_pid
    $phpPid=[int]$state.php_pid
    $oldProc=Proc $oldPid
    $stamp=if($null -ne $oldProc){([datetime]$oldProc.CreationDate).ToUniversalTime().ToString('o')}else{''}
    $already=Owned $oldPid 'Caddyfile.dev-lab-assistant-candidate' $stamp
    if($already) {
        if(-not(WaitPorts $oldPid $allPorts) -or -not(CheckHttp $allPorts)){throw 'EZS_CADDY_ALREADY_CUTOVER_UNHEALTHY'}
        Write-Host 'EZS_CADDY_LA_CUTOVER_ALREADY_ACTIVE'
        return
    }
    if(-not(Owned $oldPid 'Caddyfile.dev-root-candidate' $stamp)){throw 'EZS_CADDY_OLD_OWNER_NOT_ATTESTED'}
    if(-not(WaitPorts $oldPid $requiredPorts)){throw 'EZS_CADDY_OLD_LISTENERS_UNVERIFIED'}
    foreach($port in @(8702,8712)) {
        if(@(Listener $port).Count -gt 0){throw "EZS_CADDY_REFUSED_FOREIGN_LISTENER_$port"}
    }
    if($Action -eq 'status'){Write-Host 'EZS_CADDY_LA_CUTOVER_PENDING';return}
    foreach($port in @(8701,8713)){
        if(@(Listener $port).Count -ne 1){throw "EZS_CADDY_BACKEND_UNAVAILABLE_$port"}
    }
    # Shared Caddy keeps its existing EZScore DEV route: resolve this infrastructure
    # value internally, without asking LAB/Assistant operators to configure EZScore.
    $devMediaRoot='H:\EZScore_dev\var\storage\stems'
    if(-not(Test-Path -LiteralPath $devMediaRoot -PathType Container)){
        throw 'EZS_CADDY_EXISTING_DEV_MEDIA_DIRECTORY_MISSING'
    }
    $env:EZSCORE_MEDIA_ROOT=$devMediaRoot
    if(-not(CheckHttp $requiredPorts)){throw 'EZS_CADDY_BASELINE_HTTP_UNHEALTHY'}
    $oldArgs=@('run','--config',('"' + $oldConfig + '"'),'--adapter','caddyfile')
    $newArgs=@('run','--config',('"' + $newConfig + '"'),'--adapter','caddyfile')
    $started=$null
    $rollback=$null
    try {
        if(-not(Owned $oldPid 'Caddyfile.dev-root-candidate' $stamp)){throw 'EZS_CADDY_OWNER_CHANGED'}
        Stop-Process -Id $oldPid -ErrorAction Stop
        for($i=0;$i -lt 40;$i++) {
            $busy=@($requiredPorts | Where-Object {@(Listener $_).Count -gt 0})
            if($null -eq (Proc $oldPid) -and $busy.Count -eq 0){break}
            Start-Sleep -Milliseconds 250
        }
        foreach($port in $requiredPorts) {
            if(@(Listener $port).Count -gt 0){throw "EZS_CADDY_OLD_PORT_STILL_BUSY_$port"}
        }
        $started=Start-Process -FilePath $caddy -ArgumentList $newArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru
        if(-not(WaitPorts ([int]$started.Id) $allPorts)){throw 'EZS_CADDY_NEW_LISTENERS_NOT_READY'}
        if(-not(CheckHttp $allPorts)){throw 'EZS_CADDY_NEW_HTTP_FAILED'}
        $state.caddy_pid=[int]$started.Id
        [IO.File]::WriteAllText($statePath,($state|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_CADDY_LA_CUTOVER_OK_8790_8502_8852_8702_8712'
    }catch {
        $reason=$_
        if($null -ne $started -and (Owned ([int]$started.Id) 'Caddyfile.dev-lab-assistant-candidate' '')){
            Stop-Process -Id $started.Id -ErrorAction SilentlyContinue
        }
        for($i=0;$i -lt 40;$i++) {
            $busy=@($allPorts | Where-Object {@(Listener $_).Count -gt 0})
            if($busy.Count -eq 0){break}
            Start-Sleep -Milliseconds 250
        }
        if(@($allPorts | Where-Object {@(Listener $_).Count -gt 0}).Count -eq 0){
            $rollback=Start-Process -FilePath $caddy -ArgumentList $oldArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru
            if(WaitPorts ([int]$rollback.Id) $requiredPorts) {
                $state.caddy_pid=[int]$rollback.Id
                [IO.File]::WriteAllText($statePath,($state|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
                Write-Host 'EZS_CADDY_ROLLBACK_OLD_CONFIG_RESTORED'
            }else{Write-Host 'EZS_CADDY_ROLLBACK_FAILED_MANUAL_DIAGNOSTIC_REQUIRED'}
        }else {Write-Host 'EZS_CADDY_ROLLBACK_REFUSED_PORT_OWNERSHIP_UNCERTAIN'}
        throw $reason
    }
}finally{if($null -ne $lock){$lock.Dispose()}}
