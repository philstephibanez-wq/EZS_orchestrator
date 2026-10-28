<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['AddSeconds(45)','HttpReady 8502','HttpReady 8852','$devReady','$previewReady','EZS_DEV_APP_HTTP_NOT_READY'] as $needle){
 if(!str_contains($s,$needle))throw new RuntimeException('START_READINESS_MISSING:'.$needle);
}
if(str_contains($s,"if(-not(HttpReady 8502 '/fr/login') -or -not(HttpReady 8852 '/fr/login'))"))throw new RuntimeException('SHORT_CIRCUIT_REGRESSION');
echo "EZS_DEV_HTTP_WARMUP_2_B5_CONTRACT_OK\n";
