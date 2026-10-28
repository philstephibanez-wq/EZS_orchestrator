<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
foreach (['param([switch]$RefreshDevApps)','if($RefreshDevApps)','IsOwned $target.port $target.processId $target.stamp','EZS_DEV_APPS_REFRESH_OWNED_ONLY_OK',"\$env:EZSCORE_INSTANCE='dev'"] as $token){
 if(!str_contains($start,$token))throw new RuntimeException('REFRESH_CONTRACT_MISSING:'.$token);
}
if(str_contains($start,'prod_mode.php')||str_contains($start,"-Action stop"))throw new RuntimeException('PROD_OR_GLOBAL_STOP_IN_START');
if(!str_contains($stop,'$entry maintenance'))throw new RuntimeException('STOP_MAINTENANCE_REGRESSION');
if(strpos($start,'Stop-Process -Id $target.processId')<strpos($start,'IsOwned $target.port $target.processId $target.stamp'))throw new RuntimeException('IDENTITY_NOT_CHECKED_FIRST');
echo "EZS_DEV_REFRESH_BADGE_2_B7_CONTRACT_OK\n";
