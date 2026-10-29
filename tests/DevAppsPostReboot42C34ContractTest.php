<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2c34')throw new RuntimeException('VERSION');
$s=(string)file_get_contents($r.'/scripts/start.ps1');
foreach(['EZS_DEV_APPS_STALE_STATE_AFTER_REBOOT_CLEARED',
 'EZS_DEV_APP_REFUSED_STALE_STATE',
 'Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$s.dev_pid)"',
 'Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$s.preview_pid)"',
 '@(Owners 8602).Count -gt 0','@(Owners 8862).Count -gt 0',
 'Remove-Item -LiteralPath $stateFile -Force -ErrorAction Stop',
 'Invoke-EzsLabAssistantLifecycle -Action start',
 'Invoke-EzsAssistantAiLifecycle -Action start'] as $part){
 if(!str_contains($s,$part))throw new RuntimeException('MISSING_GUARD: '.$part);
}
if(strpos($s,'EZS_DEV_APPS_STALE_STATE_AFTER_REBOOT_CLEARED') > strpos($s,'foreach($port in @(8602,8862))'))throw new RuntimeException('RECOVERY_TOO_LATE');
echo "EZS_DEV_APPS_POST_REBOOT_4_2C34_OK\n";
