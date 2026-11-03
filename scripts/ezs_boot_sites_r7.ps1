[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','Boot','HardStatus')][string]$Action)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root='H:\EZS_orchestrator'
$adapter=Join-Path $root 'scripts\ezs_platform_control.ps1'
$maintenance=Join-Path $root 'runtime\supervision\prod-maintenance-mode-r6b.json'
$lockDir=Join-Path $root 'runtime\supervision'
$logFile=Join-Path $lockDir 'site-boot-r7.jsonl'
$utf8=New-Object System.Text.UTF8Encoding($false)
if (!(Test-Path -LiteralPath $lockDir -PathType Container)){New-Item -ItemType Directory -Path $lockDir -Force|Out-Null}
$mutex=New-Object Threading.Mutex($false,'Local\EZS_SITE_BOOT_R7')
$locked=$false
function Emit([string]$site,[string]$event,[string]$reason=''){
  $row=[ordered]@{timestamp_utc=[DateTime]::UtcNow.ToString('o');site=$site;event=$event;reason=$reason;phase=$Action}
  $json=ConvertTo-Json -Compress -InputObject $row
  [IO.File]::AppendAllText($logFile,$json+"`n",$utf8)
  Write-Output $json
}
function Mode {
  if (!(Test-Path -LiteralPath $maintenance -PathType Leaf)){return 'NORMAL'}
  $x=Get-Content -LiteralPath $maintenance -Raw -Encoding UTF8|ConvertFrom-Json -ErrorAction Stop
  if ($x.schema -ne 'ezs.prod-maintenance-mode.r6b' -or $x.mode -notin @('NORMAL','MAINTENANCE','TRANSITION','FAILED')){throw 'EZS_R7_MAINTENANCE_MODE_INVALID'}
  return [string]$x.mode
}
function Evidence([string]$site){
  $lines=@(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $adapter -Site $site -Action Status 2>&1)
  if ($LASTEXITCODE -ne 0){throw ('EZS_R7_STATUS_FAILED_'+$site)}
  $rows=@($lines|Where-Object{[string]$_ -match '^HARD_SITE='})
  if ($rows.Count -ne 1){throw ('EZS_R7_HARD_EVIDENCE_MISSING_'+$site)}
  $pattern='^HARD_SITE=(dev|lab|assistant|prod) STATE=(RUNNING|ABSENT|UNVERIFIED) PROCESSES=(\d+) PORTS=(\d+) EXPECTED=(\d+) REASON=([A-Z_]+) RECORD=(True|False)$'
  $m=[regex]::Match([string]$rows[0],$pattern)
  if (!$m.Success -or $m.Groups[1].Value -ne $site){throw 'EZS_R7_HARD_EVIDENCE_INVALID'}
  $expected=if($site -in @('assistant','prod')){3}else{2}
  if([int]$m.Groups[5].Value -ne $expected){throw 'EZS_R7_HARD_EXPECTED_PORTS_INVALID'}
  return @{state=$m.Groups[2].Value;owned=[int]$m.Groups[3].Value;
    listeners=[int]$m.Groups[4].Value;expected=$expected;reason=$m.Groups[6].Value;
    recorded=$m.Groups[7].Value}
}
try {
  try {$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true}
  if (!$locked){throw 'EZS_R7_BOOT_LOCK_BUSY'}
  if (!(Test-Path -LiteralPath $adapter -PathType Leaf)){throw 'EZS_R7_PLATFORM_ADAPTER_MISSING'}
  $mode=Mode
  $sites=@('dev','lab','assistant','prod')
  $failures=0
  foreach($site in $sites){
    if($site -eq 'prod' -and $mode -ne 'NORMAL'){
      Emit $site 'SKIPPED_PROD_MAINTENANCE' $mode
      continue
    }
    try {
      $before=Evidence $site
      Emit $site ('BEFORE_'+$before.state) ('processes='+$before.owned+' ports='+$before.listeners+' reason='+$before.reason+' record='+$before.recorded)
      if($Action -eq 'HardStatus'){if($before.state -ne 'RUNNING' -and !($site -eq 'prod' -and $mode -ne 'NORMAL')){$failures++};continue}
      if($before.state -eq 'RUNNING'){Emit $site 'ALREADY_RUNNING';continue}
      if($before.state -ne 'ABSENT') {Emit $site 'BLOCKED_AMBIGUOUS' 'No adoption and no process termination';$failures++;continue}
      $result=@(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $adapter -Site $site -Action Preflight 2>&1)
      if($LASTEXITCODE -ne 0){throw ('EZS_R7_PREFLIGHT_FAILED_'+$site)}
      if($Action -eq 'Preflight'){Emit $site 'PREFLIGHT_OK_NO_START';continue}
      # One explicit Boot pass: no automatic retries from subsequent polling cycles.
      $result=@(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $adapter -Site $site -Action Start 2>&1)
      if($LASTEXITCODE -ne 0){throw ('EZS_R7_START_FAILED_'+$site)}
      Start-Sleep -Milliseconds 900
      $after=Evidence $site
      if($after.state -ne 'RUNNING'){
        Emit $site 'START_UNVERIFIED' ('processes='+$after.owned+' ports='+$after.listeners+' reason='+$after.reason)
        $failures++;continue
      }
      Emit $site 'HARD_ATTESTED_RUNNING' ('listeners='+$after.listeners)
    }catch{Emit $site 'ERROR' $_.Exception.Message;$failures++}
  }
  if($failures -gt 0){throw ('EZS_R7_BOOT_INCOMPLETE_'+$failures)}
  Write-Host ('EZS_R7_'+$Action.ToUpperInvariant()+'_OK')
}catch{Write-Error $_;exit 2}
finally{if($locked){$mutex.ReleaseMutex()};$mutex.Dispose()}
