[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateSet('Preflight','Status','Start','Stop')][string]$Action
)
$ErrorActionPreference='Stop'
$orchestrator='H:\EZS_orchestrator'
$assistant='H:\EZStudioLab_assistant'
$intentPath=Join-Path $orchestrator 'runtime\supervision\desired-services.json'
$start=Join-Path $assistant 'scripts\start.ps1'
$stop=Join-Path $assistant 'scripts\stop.ps1'
function Read-Desired {
  if (!(Test-Path -LiteralPath $intentPath -PathType Leaf)) {throw 'ASSISTANT_INTENT_MISSING'}
  $d=Get-Content -LiteralPath $intentPath -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop
  if ($d.schema -ne 'ezs.desired-services.v1'){throw 'ASSISTANT_INTENT_SCHEMA_INVALID'}
  $v=$d.services.PSObject.Properties['assistant']
  if ($null -eq $v -or [string]$v.Value -notin @('RUNNING','STOPPED')) {throw 'ASSISTANT_INTENT_INVALID'}
  [string]$v.Value
}
function Assert-Canonical {
  foreach($f in @($start,$stop)) {if (!(Test-Path -LiteralPath $f -PathType Leaf)){throw ('ASSISTANT_CANONICAL_SCRIPT_MISSING '+$f)}}
  $startText=Get-Content -LiteralPath $start -Raw -ErrorAction Stop
  $stopText=Get-Content -LiteralPath $stop -Raw -ErrorAction Stop
  if($startText -notmatch 'llama-server\.exe' -or $startText -notmatch '8720' -or $startText -notmatch 'start-web\.ps1') {throw 'ASSISTANT_START_LLAMA_CONTRACT_INVALID'}
  if($stopText -notmatch 'llama-server\.exe' -or $stopText -notmatch '8720' -or $stopText -notmatch 'ASSISTANT_SAFE_STOP_REFUSED') {throw 'ASSISTANT_STOP_LLAMA_CONTRACT_INVALID'}
}
$desired=Read-Desired
Assert-Canonical
if($Action -eq 'Preflight') {Write-Host ('ASSISTANT_LLAMA_CANONICAL_PREFLIGHT_OK INTENT='+$desired);exit 0}
if($Action -eq 'Status') {
  $ports=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.LocalPort -in @(8712,8720)}|Select-Object LocalAddress,LocalPort,OwningProcess)
  Write-Host ('ASSISTANT_DESIRED='+$desired)
  $ports|Format-Table -AutoSize
  Write-Host 'ASSISTANT_LLAMA_STATUS_READONLY'
  exit 0
}
if($Action -eq 'Start' -and $desired -ne 'RUNNING'){throw 'ASSISTANT_START_REFUSED_DESIRED_STOPPED'}
if($Action -eq 'Stop' -and $desired -ne 'STOPPED'){throw 'ASSISTANT_STOP_REFUSED_DESIRED_RUNNING'}
# Never start/stop Llama directly: the Assistant owns its entire lifecycle.
$entry=if($Action -eq 'Start'){$start}else{$stop}
$before=Read-Desired
if($before -ne $desired){throw 'ASSISTANT_INTENT_CHANGED'}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $entry
if($LASTEXITCODE -ne 0){throw ('ASSISTANT_CANONICAL_'+$Action+'_FAILED_'+$LASTEXITCODE)}
Write-Host ('ASSISTANT_LLAMA_COUPLED_'+$Action.ToUpperInvariant()+'_SCRIPT_OK')
