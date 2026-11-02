# Independent ROOT-only task; the historic DEV/PROD task is never modified.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('Preflight','InstallDisabled','Enable','Status','Disable','Remove')][string]$Action)
$ErrorActionPreference = 'Stop'
$root = 'H:\EZS_orchestrator'
$name = 'EZS_ROOT_resident'
$legacy = 'EZS_orchestrator_supervisor'
$hidden = Join-Path $root 'scripts\ezs_supervisor_resident_hidden.vbs'
$resident = Join-Path $root 'scripts\ezs_supervisor_resident.ps1'
$tick = Join-Path $root 'scripts\ezs_supervisor_tick.ps1'
$task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
function Assert-TaskIdentity($item) {
    if ($null -eq $item -or $item.Actions.Count -ne 1) { throw 'EZS_ROOT_TASK_IDENTITY_UNKNOWN' }
    $a = $item.Actions[0]
    if ($a.Execute -notmatch '(?i)(?:^|\\)wscript\.exe$' -or
        $a.Arguments -notlike '*ezs_supervisor_resident_hidden.vbs*') { throw 'EZS_ROOT_TASK_FOREIGN_REFUSED' }
}
if ($Action -eq 'Status') {
    if ($null -eq $task) { Write-Host 'EZS_ROOT_TASK_ABSENT'; exit 0 }
    Assert-TaskIdentity $task
    $task | Select-Object TaskName,State
    Get-ScheduledTaskInfo -TaskName $name | Select-Object LastRunTime,LastTaskResult,NextRunTime
    exit 0
}
if ((Get-Content (Join-Path $root 'VERSION') -Raw).Trim() -ne '4.2d35') { throw 'EZS_ROOT_TASK_VERSION_MISMATCH' }
if (!(Test-Path $hidden -PathType Leaf) -or !(Test-Path $resident -PathType Leaf) -or !(Test-Path $tick -PathType Leaf)) { throw 'EZS_ROOT_TASK_SOURCES_MISSING' }
if ($Action -eq 'Preflight' -or $Action -eq 'InstallDisabled' -or $Action -eq 'Enable') {
    $old = Get-ScheduledTask -TaskName $legacy -ErrorAction Stop
    if ($old.State -ne 'Disabled') { throw 'EZS_ROOT_LEGACY_TASK_MUST_REMAIN_DISABLED' }
}
if ($Action -eq 'Preflight') {
    if ($null -ne $task) { Assert-TaskIdentity $task; throw 'EZS_ROOT_TASK_ALREADY_EXISTS' }
    Write-Host 'EZS_ROOT_RESIDENT_PREFLIGHT_OK'; exit 0
}
if ($Action -eq 'InstallDisabled') {
    if ($null -ne $task) { throw 'EZS_ROOT_TASK_ALREADY_EXISTS' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
    $taskExecAction = New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument ('//B //Nologo "' + $hidden + '"') -WorkingDirectory $root
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -Disable
    Register-ScheduledTask -TaskName $name -Action $taskExecAction -Trigger $trigger -Settings $settings -Principal $principal -Description 'EZS ROOT 8790/8791 only; independent resident; no PROD/DEV Caddy' -ErrorAction Stop | Out-Null
    $created = Get-ScheduledTask -TaskName $name -ErrorAction Stop
    Assert-TaskIdentity $created
    if ($created.State -ne 'Disabled') { Disable-ScheduledTask -TaskName $name | Out-Null; throw 'EZS_ROOT_TASK_NOT_DISABLED' }
    Write-Host 'EZS_ROOT_RESIDENT_INSTALLED_DISABLED'; exit 0
}
Assert-TaskIdentity $task
if ($Action -eq 'Enable') {
    Enable-ScheduledTask -TaskName $name | Out-Null
    Start-ScheduledTask -TaskName $name
    Write-Host 'EZS_ROOT_RESIDENT_ENABLED_CHECK_RUNTIME'; exit 0
}
if ($Action -eq 'Disable') {
    Disable-ScheduledTask -TaskName $name | Out-Null
    if ((Get-ScheduledTask -TaskName $name).State -eq 'Running') { Stop-ScheduledTask -TaskName $name }
    Write-Host 'EZS_ROOT_RESIDENT_DISABLED'; exit 0
}
if ($Action -eq 'Remove') {
    if ($task.State -ne 'Disabled') { throw 'EZS_ROOT_TASK_DISABLE_FIRST' }
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host 'EZS_ROOT_RESIDENT_REMOVED'; exit 0
}
