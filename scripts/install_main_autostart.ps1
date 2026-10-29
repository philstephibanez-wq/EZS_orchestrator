param([switch]$Remove)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$entry=Join-Path $root 'scripts\start.ps1'
$name='EZS_MAIN_START_AFTER_LOGON'
if(-not(Test-Path -LiteralPath $entry -PathType Leaf)){throw 'EZS_AUTOSTART_ENTRY_MISSING'}
if($Remove){
 Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop
 Write-Host 'EZS_MAIN_AUTOSTART_REMOVED'
 return
}
# Logon trigger deliberately runs under the SAME Windows user (DPAPI,
# mapped drives and H:\ paths); cannot safely be launched as SYSTEM at boot.
# Does not run START during installation and does not touch existing services.
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
if([string]::IsNullOrWhiteSpace($identity)){throw 'EZS_AUTOSTART_USER_MISSING'}
$ps=Join-Path $PSHOME 'powershell.exe'
$action=New-ScheduledTaskAction -Execute $ps -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$entry+'"') -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([timespan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force -ErrorAction Stop | Out-Null
Write-Host "EZS_MAIN_AUTOSTART_REGISTERED name=$name user=$identity trigger=AT_LOGON"
Write-Host 'EZS_MAIN_AUTOSTART_REQUIRES_USER_LOGON_AFTER_REBOOT'
