<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$s=(string)file_get_contents($root.'/scripts/stop.ps1');
$c=(string)file_get_contents($root.'/bin/prod_mode.php');
$mode=(string)file_get_contents($root.'/src/Module/Infrastructure/ProdModeService.php');
$pre=strpos($s,'$entry maintenance');
$dev=strpos($s,"v2_lifecycle.ps1') -Action stop");
if($pre===false||$dev===false||$pre>=$dev)throw new RuntimeException('MAINTENANCE_MUST_PRECEDE_DEV_STOP');
if(!str_contains($s,'if($LASTEXITCODE -ne 0)')||!str_contains($s,'EZS_STOP_REFUSED_PROD_MAINTENANCE_UNCONFIRMED'))throw new RuntimeException('FAIL_CLOSED_MISSING');
foreach(['Stop-Process','prod_lifecycle.ps1','gateway-php.json','-Target gateway'] as $needle)if(str_contains($s,$needle))throw new RuntimeException('STOP_PROD_PROCESS_REGRESSION:'.$needle);
if(!str_contains($c,'ProdModeService')||!str_contains($c,'$service->apply($action)'))throw new RuntimeException('PHP_MODE_ENTRY_MISSING');
if(!str_contains($mode,'prod_maintenance_http_not_confirmed')||!str_contains($mode,"$"."public['status'] !== 503"))throw new RuntimeException('MAINTENANCE_HTTP_CHECK_MISSING');
echo "EZS_STOP_FORCE_PROD_MAINTENANCE_CONTRACT_OK\n";
