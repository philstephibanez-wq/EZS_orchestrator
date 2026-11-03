[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Start','Stop','Status','Preflight')][string]$Action,
    [Parameter(Mandatory=$true)][ValidateSet('prod','dev','lab')][string]$Site
)
$ErrorActionPreference='Stop'
$root='H:\EZS_orchestrator'
$exe='H:\FRANKENPHP\bin\frankenphp.exe'
$config=Join-Path $root ('config\frankenphp\Caddyfile.'+$Site+'.native')
$intentFile=Join-Path $root 'runtime\supervision\desired-services.json'
$ports=if($Site -eq 'prod') {@(8501,8510,8511)}elseif($Site -eq 'dev'){@(8502,8602)}else{@(8702,8701)}
$stateDir=Join-Path $root 'runtime\native-sites'
$recordFile=Join-Path $stateDir ($Site+'.json')
function Read-Intent {
    if(!(Test-Path -LiteralPath $intentFile -PathType Leaf)){throw 'INTENT_MISSING'}
    $s=Get-Content -LiteralPath $intentFile -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop
    if($s.schema -ne 'ezs.desired-services.v1'){throw 'INTENT_SCHEMA_INVALID'}
    $prop=$s.services.PSObject.Properties[$Site]
    if($null -eq $prop -or [string]$prop.Value -notin @('RUNNING','STOPPED')){throw 'INTENT_SITE_INVALID'}
    [string]$prop.Value
}
function Owned {
    @(Get-CimInstance Win32_Process -ErrorAction Stop|Where-Object {
        [string]$_.ExecutablePath -ieq $exe -and
        [string]$_.CommandLine -match '(?i)(?:^|\s)run(?:\s|$)' -and
        [string]$_.CommandLine.Replace('/','\').IndexOf($config.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}
function Ports-Occupied {
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.LocalPort -in $ports})
}
function Record {
    if(!(Test-Path -LiteralPath $recordFile -PathType Leaf)){return $null}
    $s=Get-Content -LiteralPath $recordFile -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop
    if($s.schema -ne 'ezs.native-site.owner.v1' -or $s.site -ne $Site){throw 'OWNER_RECORD_INVALID'}
    $s
}
function Assert-Files {
    if(!(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'FRANKENPHP_EXE_MISSING'}
    if(!(Test-Path -LiteralPath $config -PathType Leaf)){throw 'NATIVE_CONFIG_MISSING'}
    $caddyText=Get-Content -LiteralPath $config -Raw -Encoding UTF8 -ErrorAction Stop
    if($caddyText -match '(?i)\bphp_fastcgi\b|\bphp-cgi\b'){throw 'NATIVE_CONFIG_LEGACY_FASTCGI_REFUSED'}
    $entries=if($Site -eq 'prod'){@('H:\EZScore\public\index.php','H:\EZS_orchestrator\runtime_components\prod_gateway_php\router.php')}elseif($Site -eq 'dev'){@('H:\EZScore_dev\public\index.php')}else{@('H:\EZStudio_lab\public\index.php')}
    foreach($d in $entries){
        if(!(Test-Path -LiteralPath $d -PathType Leaf)){throw ('PHP_ENTRY_MISSING '+$d)}
    }
}
if($Action -eq 'Status') {
    $processes=@(Owned);$listeners=@(Ports-Occupied)
    Write-Host "SITE=$Site INTENT=$(Read-Intent) OWNED=$($processes.Count) LISTENERS=$($listeners.Count)"
    $processes|Select-Object ProcessId,CreationDate
    $listeners|Select-Object LocalAddress,LocalPort,OwningProcess
    exit 0
}
Assert-Files
$desired=Read-Intent
$owned=@(Owned);$listeners=@(Ports-Occupied);$record=Record
if($Action -eq 'Preflight') {
    Write-Host "NATIVE_PREFLIGHT_SITE=$Site INTENT=$desired OWNED=$($owned.Count) LISTENERS=$($listeners.Count)"
    if($owned.Count -gt 1){throw 'MULTIPLE_OWNED'}
    if($listeners.Count -gt 0 -and $owned.Count -eq 0){throw 'FOREIGN_LISTENER'}
    exit 0
}
if($Action -eq 'Start') {
    if($Site -eq 'prod' -and $desired -ne 'RUNNING'){throw 'PROD_START_REQUIRES_EXPLICIT_RUNNING_INTENT'}
    if($desired -ne 'RUNNING'){throw 'INTENT_STOPPED_REFUSED'}
    if($owned.Count -ne 0 -or $listeners.Count -ne 0 -or $null -ne $record){throw 'ALREADY_RUNNING_OR_STALE_OWNER_REFUSED'}
    if($Site -eq 'dev' -and [string]$env:EZSCORE_MEDIA_ROOT -eq ''){throw 'DEV_MEDIA_ROOT_ENV_MISSING'}
    if(!(Test-Path -LiteralPath $stateDir -PathType Container)){New-Item -ItemType Directory -Force -Path $stateDir|Out-Null}
    $oldEnv=[Environment]::GetEnvironmentVariable('APP_ENV','Process')
    $oldDebug=[Environment]::GetEnvironmentVariable('APP_DEBUG','Process')
    try {
        [Environment]::SetEnvironmentVariable('APP_ENV',$(if($Site -eq 'prod'){'prod'}else{'dev'}),'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG',$(if($Site -eq 'prod'){'0'}else{'1'}),'Process')
        $p=Start-Process -FilePath $exe -ArgumentList @('run','--config',('"'+$config+'"'),'--adapter','caddyfile') -WorkingDirectory $root -PassThru -WindowStyle Hidden -ErrorAction Stop
    } finally {
        [Environment]::SetEnvironmentVariable('APP_ENV',$oldEnv,'Process')
        [Environment]::SetEnvironmentVariable('APP_DEBUG',$oldDebug,'Process')
    }
    $info=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction Stop
    if($null -eq $info){throw 'START_PROCESS_NOT_FOUND'}
    $recordObject=[ordered]@{schema='ezs.native-site.owner.v1';site=$Site;pid=[int]$p.Id;creation=[string]$info.CreationDate;config=$config}
    [IO.File]::WriteAllText($recordFile,((ConvertTo-Json -Compress $recordObject)+"`n"),(New-Object Text.UTF8Encoding($false)))
    Write-Host "NATIVE_SITE_STARTED=$Site PID=$($p.Id)"
    exit 0
}
if($Action -eq 'Stop') {
    if($Site -eq 'prod'){throw 'PROD_STOP_PROTECTED_REFUSED'}
    if($desired -ne 'STOPPED'){throw 'INTENT_RUNNING_REFUSED_STOP'}
    if($null -eq $record -or $owned.Count -ne 1){throw 'NO_UNAMBIGUOUS_OWNED_PROCESS'}
    $p=$owned[0]
    if([int]$record.pid -ne [int]$p.ProcessId -or [string]$record.creation -ne [string]$p.CreationDate){throw 'PROCESS_IDENTITY_CHANGED'}
    $again=@(Owned)
    if($again.Count -ne 1 -or [int]$again[0].ProcessId -ne [int]$record.pid -or [string]$again[0].CreationDate -ne [string]$record.creation){throw 'PROCESS_IDENTITY_REATTEST_FAILED'}
    Stop-Process -Id ([int]$record.pid) -ErrorAction Stop
    Remove-Item -LiteralPath $recordFile -Force -ErrorAction Stop
    Write-Host "NATIVE_SITE_STOP_REQUESTED=$Site"
}
