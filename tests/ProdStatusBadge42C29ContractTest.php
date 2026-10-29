<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2c29')throw new RuntimeException('VERSION');
$s=(string)file_get_contents($r.'/public/assets/ezs-prod-control.js');
foreach(["setStatus('Gateway et Symfony actifs','success')","setStatus('Gateway active, backend indisponible','warning')","setStatus('Gateway absente','danger')","setStatus('État indisponible','secondary')"] as $expect){
 if(!str_contains($s,$expect))throw new RuntimeException('PROD_BADGE_STATE');
}
if(!str_contains($s,"removeClass('text-bg-secondary text-bg-success text-bg-warning text-bg-danger')"))throw new RuntimeException('PROD_BADGE_STALE_CLASS');
$t=(string)file_get_contents($r.'/tests/QueueRestRead42C27ContractTest.php');
if(str_contains($t,"!=='4.2c27'"))throw new RuntimeException('LEGACY_VERSION_GATE');
echo "EZS_PROD_STATUS_BADGE_4_2C29_OK\n";
