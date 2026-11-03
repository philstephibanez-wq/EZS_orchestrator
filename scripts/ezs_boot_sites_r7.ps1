# R8: a web server bootstrap is a single platform operation. No per-site PID lifecycle.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','Boot','HardStatus')][string]$Action)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='H:\EZS_orchestrator'
$exe='H:\FRANKENPHP\bin\frankenphp.exe'
$modeFile=Join-Path $root 'runtime\supervision\prod-maintenance-mode-r6b.json'
$logDir=Join-Path $root 'runtime\supervision'
$logFile=Join-Path $logDir 'site-boot-r8.jsonl'
$utf8=New-Object Text.UTF8Encoding($false)
$mutex=New-Object Threading.Mutex($false,'Local\EZS_WEB_BOOT_R8')
$locked=$false
$sites=[ordered]@{
    dev=@{ports=@(8502,8602);url='http://127.0.0.1:8502/fr/catalog';config='Caddyfile.dev.native';entry='H:\EZScore_dev\public\index.php'}
    lab=@{ports=@(8702,8701);url='http://127.0.0.1:8702/';config='Caddyfile.lab.native';entry='H:\EZStudio_lab\public\index.php'}
    assistant=@{ports=@(8712,8713);url='http://127.0.0.1:8712/';config='Caddyfile.assistant.native';entry='H:\EZStudioLab_assistant\public\index.php'}
    prod=@{ports=@(8501,8510,8511);url='http://127.0.0.1:8501/fr/catalog';config='Caddyfile.prod.native';entry='H:\EZScore\public\index.php'}
}
function Mode {
    if(!(Test-Path -LiteralPath $modeFile -PathType Leaf)){return 'NORMAL'}
    $m=Get-Content -LiteralPath $modeFile -Raw -Encoding UTF8|ConvertFrom-Json -ErrorAction Stop
    if($m.schema -ne 'ezs.prod-maintenance-mode.r6b' -or $m.mode -notin @('NORMAL','MAINTENANCE','TRANSITION','FAILED')){throw 'EZS_R8_MODE_INVALID'}
    return [string]$m.mode
}
function Open-Ports([int[]]$ports){
    $opened=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object{$_.LocalPort -in $ports}|Select-Object -ExpandProperty LocalPort -Unique)
    return @($opened)
}
function Web-Http([string]$url){
    $request=[Net.HttpWebRequest]([Net.WebRequest]::Create($url))
    $request.Timeout=2500
    $request.AllowAutoRedirect=$false
    try {
        $response=[Net.HttpWebResponse]$request.GetResponse()
        try{return [int]$response.StatusCode}finally{$response.Close()}
    } catch [Net.WebException] {
        if($null -ne $_.Exception.Response){
            $response=$_.Exception.Response
            try{return [int]$response.StatusCode}finally{$response.Close()}
        }
        return 0
    }
}
function Output-Record([string]$site,[string]$event,[string]$detail){
    $record=[ordered]@{timestamp_utc=[DateTime]::UtcNow.ToString('o');site=$site;event=$event;detail=$detail;action=$Action}
    $json=ConvertTo-Json -Compress -InputObject $record
    if($Action -eq 'Boot'){
        if(!(Test-Path -LiteralPath $logDir -PathType Container)){New-Item -ItemType Directory -Path $logDir -Force|Out-Null}
        [IO.File]::AppendAllText($logFile,$json+"`n",$utf8)
    }
    Write-Output $json
}
function Status([string]$name,[hashtable]$spec,[string]$mode){
    $open=@(Open-Ports $spec.ports)
    $status=Web-Http $spec.url
    $missing=@($spec.ports|Where-Object{$_ -notin $open})
    $maintenance=$name -eq 'prod' -and $status -eq 503
    $state=if($maintenance -and 8501 -in $open){'MAINTENANCE'}elseif($missing.Count -eq 0 -and $status -ge 200 -and $status -lt 400){'OK'}elseif($open.Count -eq 0){'ABSENT'}else{'PARTIAL'}
    return @{state=$state;opened=$open;missing=$missing;http=$status}
}
function Start-Web([string]$name,[hashtable]$spec){
    $config=Join-Path $root ('config\frankenphp\'+$spec.config)
    foreach($file in @($exe,$config,$spec.entry)){
        if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('EZS_R8_REQUIRED_FILE_MISSING '+$file)}
    }
    if($name -eq 'prod'){
        $gateway='H:\EZS_orchestrator\runtime_components\prod_gateway_php\router.php'
        if(!(Test-Path -LiteralPath $gateway -PathType Leaf)){throw 'EZS_R8_PROD_GATEWAY_MISSING'}
    }
    $previousMedia=[Environment]::GetEnvironmentVariable('EZSCORE_MEDIA_ROOT','Process')
    if($name -eq 'dev'){
        $media='H:\EZScore_dev\var\storage\stems'
        if(!(Test-Path -LiteralPath $media -PathType Container)){throw 'EZS_R8_DEV_MEDIA_ROOT_MISSING'}
        $env:EZSCORE_MEDIA_ROOT=$media
    }
    # PROD cutover to EZS_maintenance still requires its canonical native owner record.
    # Keep this boundary intact; hard pings themselves never inspect PID.
    if($name -eq 'prod'){
        $adapter=Join-Path $root 'scripts\ezs_platform_control.ps1'
        if(!(Test-Path -LiteralPath $adapter -PathType Leaf)){throw 'EZS_R8_PROD_ADAPTER_MISSING'}
        foreach($phase in @('Preflight','Start')){
            & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $adapter -Site prod -Action $phase
            if($LASTEXITCODE -ne 0){throw ('EZS_R8_PROD_'+$phase.ToUpperInvariant()+'_FAILED')}
        }
        return
    }
    $previousEnv=[Environment]::GetEnvironmentVariable('APP_ENV','Process')
    $previousDbg=[Environment]::GetEnvironmentVariable('APP_DEBUG','Process')
    try {
        [Environment]::SetEnvironmentVariable('APP_ENV',$(if($name -eq 'prod'){'prod'}else{'dev'}),'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG',$(if($name -eq 'prod'){'0'}else{'1'}),'Process')
        # No saved PID, no stop, no user-facing console.
        $null=Start-Process -FilePath $exe -ArgumentList @('run','--config',('"'+$config+'"'),'--adapter','caddyfile') -WorkingDirectory $root -WindowStyle Hidden -PassThru -ErrorAction Stop
    } finally {
        [Environment]::SetEnvironmentVariable('APP_ENV',$previousEnv,'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG',$previousDbg,'Process')
        [Environment]::SetEnvironmentVariable('EZSCORE_MEDIA_ROOT',$previousMedia,'Process')
    }
}
try {
    try {$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true}
    if(!$locked){throw 'EZS_R8_BOOT_ALREADY_RUNNING'}
    $mode=Mode
    $failed=0
    foreach($site in @('dev','lab','assistant','prod')){
        $spec=$sites[$site]
        if($site -eq 'prod' -and $mode -ne 'NORMAL'){
            $probe=Status $site $spec $mode
            Output-Record $site 'SKIPPED_PROD_MAINTENANCE' ('mode='+$mode+' http='+$probe.http)
            if($Action -eq 'HardStatus' -and $probe.state -ne 'MAINTENANCE'){$failed++}
            continue
        }
        try {
            $before=Status $site $spec $mode
            Output-Record $site ('HARD_'+$before.state) ('ports='+($before.opened -join ',')+' missing='+($before.missing -join ',')+' http='+$before.http)
            if($Action -eq 'HardStatus'){if($before.state -ne 'OK' -and !($site -eq 'prod' -and $before.state -eq 'MAINTENANCE')){$failed++};continue}
            if($before.state -eq 'OK' -or ($site -eq 'prod' -and $before.state -eq 'MAINTENANCE')){continue}
            if($before.state -ne 'ABSENT'){
                Output-Record $site 'BLOCKED_PARTIAL' 'Listening ports are preserved; no competing instance started'
                $failed++;continue
            }
            if($Action -eq 'Preflight'){
                Output-Record $site 'READY_TO_START' 'All configured web ports free'
                continue
            }
            Start-Web $site $spec
            $after=$null
            foreach($step in 1..20){
                Start-Sleep -Milliseconds 450
                $after=Status $site $spec $mode
                if($after.state -eq 'OK'){break}
            }
            Output-Record $site ('AFTER_'+$after.state) ('ports='+($after.opened -join ',')+' http='+$after.http)
            if($after.state -ne 'OK'){$failed++}
        }catch{Output-Record $site 'ERROR' $_.Exception.Message;$failed++}
    }
    if($failed -gt 0){throw ('EZS_R8_WEB_INCOMPLETE_'+$failed)}
    Write-Host ('EZS_R8_'+$Action.ToUpperInvariant()+'_OK')
}catch{Write-Error $_;exit 2}
finally{if($locked){$mutex.ReleaseMutex()};$mutex.Dispose()}
