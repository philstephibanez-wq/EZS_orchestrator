[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','Status','Start','Stop')][string]$Action)
$ErrorActionPreference='Stop'
$root='H:\EZS_orchestrator'
$assistant='H:\EZStudioLab_assistant'
$intentPath=Join-Path $root 'runtime\supervision\desired-services.json'
$start=Join-Path $assistant 'scripts\start.ps1'
$stop=Join-Path $assistant 'scripts\stop.ps1'
$config=Join-Path $root 'config\frankenphp\Caddyfile.assistant.native'
$franken='H:\FRANKENPHP\bin\frankenphp.exe'
function Read-Desired {
 if(!(Test-Path -LiteralPath $intentPath -PathType Leaf)){throw 'ASSISTANT_INTENT_MISSING'}
 $d=Get-Content -LiteralPath $intentPath -Raw -ErrorAction Stop|ConvertFrom-Json -ErrorAction Stop
 if($d.schema -ne 'ezs.desired-services.v1'){throw 'ASSISTANT_INTENT_SCHEMA_INVALID'}
 $v=$d.services.PSObject.Properties['assistant']
 if($null -eq $v -or [string]$v.Value -notin @('RUNNING','STOPPED')){throw 'ASSISTANT_INTENT_INVALID'}
 [string]$v.Value
}
function Assert-Canonical {
 foreach($f in @($start,$stop)){if(!(Test-Path -LiteralPath $f -PathType Leaf)){throw ('ASSISTANT_CANONICAL_SCRIPT_MISSING '+$f)}}
 $a=Get-Content -LiteralPath $start -Raw -ErrorAction Stop
 $b=Get-Content -LiteralPath $stop -Raw -ErrorAction Stop
 if($a -notmatch 'llama-server\.exe' -or $a -notmatch '8720' -or $a -notmatch 'start-web\.ps1'){throw 'ASSISTANT_START_LLAMA_CONTRACT_INVALID'}
 if($b -notmatch 'llama-server\.exe' -or $b -notmatch '8720' -or $b -notmatch 'ASSISTANT_SAFE_STOP_REFUSED'){throw 'ASSISTANT_STOP_LLAMA_CONTRACT_INVALID'}
}
$desired=Read-Desired
Assert-Canonical
if($Action -eq 'Preflight'){Write-Host ('ASSISTANT_LLAMA_CANONICAL_PREFLIGHT_OK INTENT='+$desired);exit 0}
if($Action -eq 'Status') {
 # Strict native identity evidence. Do not infer ownership from open ports alone.
 $processes=@(Get-CimInstance Win32_Process -ErrorAction Stop)
 $web=@($processes|Where-Object {
   [string]$_.ExecutablePath -ieq $franken -and
   [string]$_.CommandLine.Replace('/','\').IndexOf($config.Replace('/','\'),[StringComparison]::OrdinalIgnoreCase) -ge 0
 })
 $llama=@($processes|Where-Object {
   [string]$_.ExecutablePath -match '(?i)[\\/]llama-server\.exe$' -and
   [string]$_.CommandLine -match '(?i)(?:^|\s)(?:--port\s+)?8720(?:\s|$)'
 })
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.LocalPort -in @(8712,8713,8720)})
 $ports=@($listeners|Select-Object -ExpandProperty LocalPort -Unique)
 $valid=($web.Count -eq 1 -and $llama.Count -eq 1 -and $ports.Count -eq 3)
 if($valid){
  foreach($port in @(8712,8713)){
   if(@($listeners|Where-Object {$_.LocalPort -eq $port -and $_.OwningProcess -eq [int]$web[0].ProcessId}).Count -lt 1){$valid=$false}
  }
  if(@($listeners|Where-Object {$_.LocalPort -eq 8720 -and $_.OwningProcess -eq [int]$llama[0].ProcessId}).Count -lt 1){$valid=$false}
 }
 $owned=if($valid){1}elseif($web.Count -eq 0 -and $llama.Count -eq 0){0}else{2}
 Write-Host ('SITE=assistant INTENT='+$desired+' OWNED='+$owned+' LISTENERS='+$ports.Count)
 Write-Host 'ASSISTANT_LLAMA_STATUS_READONLY'
 exit 0
}
if($Action -eq 'Start' -and $desired -ne 'RUNNING'){throw 'ASSISTANT_START_REFUSED_DESIRED_STOPPED'}
if($Action -eq 'Stop' -and $desired -ne 'STOPPED'){throw 'ASSISTANT_STOP_REFUSED_DESIRED_RUNNING'}
# Only the Assistant's own canonical scripts may operate its web and Llama processes.
$entry=if($Action -eq 'Start'){$start}else{$stop}
if((Read-Desired) -ne $desired){throw 'ASSISTANT_INTENT_CHANGED'}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $entry
if($LASTEXITCODE -ne 0){throw ('ASSISTANT_CANONICAL_'+$Action+'_FAILED_'+$LASTEXITCODE)}
Write-Host ('ASSISTANT_LLAMA_COUPLED_'+$Action.ToUpperInvariant()+'_SCRIPT_OK')
