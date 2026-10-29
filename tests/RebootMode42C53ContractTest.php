<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
$auto=(string)file_get_contents($root.'/scripts/install_main_autostart.ps1');
foreach(['function PersistedProdMode','EZS_PROD_PERSISTED_MODE_INVALID','EZS_PROD_START_NORMAL_RESTORED','EZS_PROD_START_MAINTENANCE_OK','Invoke-EzsProdLifecycle -Action start','EZS_PROD_STALE_STATE_AFTER_REBOOT_CLEARED','Caddyfile.prod-unified'] as $key){
 if(!str_contains($start,$key))throw new RuntimeException('START_MISSING '.$key);
}
if(str_contains($start,"if(".'$target'.".name -eq 'edge_pid'){Mode ".'$true'."}"))throw new RuntimeException('START_OVERWRITES_PROD_MODE');
if(!str_contains($start,'$originalMaintenance=PersistedProdMode')||!str_contains($start,'Mode $originalMaintenance'))throw new RuntimeException('PROD_STOP_DOES_NOT_RESTORE_MODE');
if(!str_starts_with($stop,'param()')||str_contains($stop,'function Invoke-EzsProdLifecycle')||str_contains($stop,'prod_mode.php')||str_contains($stop,'EZS_PROD_STOP_OWNED_OK'))throw new RuntimeException('STOP_NOT_DEV_ONLY');
if(!str_contains($auto,'New-ScheduledTaskTrigger -AtLogOn')||!str_contains($auto,'LogonType Interactive'))throw new RuntimeException('AUTOSTART_NOT_INTERACTIVE');
echo "EZS_REBOOT_MODE_DEV_STOP_CONTRACT_OK\n";
