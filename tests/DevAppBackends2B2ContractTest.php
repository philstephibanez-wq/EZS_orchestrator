<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$s=(string)file_get_contents($root.'/scripts/start.ps1');
$t=(string)file_get_contents($root.'/scripts/stop.ps1');
foreach(['8602','8862','app-backends.json','CreationDate','EZS_DEV_APPS_READY_8502_8852','REFUSED_FOREIGN_LISTENER','HTTP_NOT_READY'] as $v){if(!str_contains($s,$v))throw new RuntimeException('START_APPS_CONTRACT_MISSING:'.$v);}
foreach(['8602','8862','app-backends.json','CreationDate','STOP_REFUSED_UNVERIFIED_OWNERSHIP','EZS_DEV_APPS_STOP_OK'] as $v){if(!str_contains($t,$v))throw new RuntimeException('STOP_APPS_CONTRACT_MISSING:'.$v);}
$a=strpos($t,'$entry maintenance');$b=strpos($t,'EZS_DEV_APPS_STOP_OK');$c=strpos($t,"v2_lifecycle.ps1') -Action stop");
if($a===false||$b===false||$c===false||!($a<$b&&$b<$c))throw new RuntimeException('MAINTENANCE_STOP_ORDER_CHANGED');
if(str_contains($s,'Stop-Process -Id 29972')||str_contains($t,'8510'))throw new RuntimeException('PROD_OR_SHARED_CADDY_REGRESSION');
echo "EZS_DEV_APP_BACKENDS_2_B2_CONTRACT_OK\n";
