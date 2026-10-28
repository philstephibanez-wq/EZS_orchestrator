<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$router=(string)file_get_contents($root.'/runtime_components/prod_gateway_php/router.php');
foreach(['Remove-Item Env:EZS_GATEWAY_RECIPE_CONFIG','Remove-Item Env:EZS_GATEWAY_RECIPE_MODE'] as $needle){
 if(!str_contains($start,$needle))throw new RuntimeException('RECIPE_ENV_ISOLATION_MISSING:'.$needle);
}
if(!str_contains($router,"(int)(\$_SERVER['SERVER_PORT']??0)===8510") || !str_contains($router,'$testConfig=false;'))
 throw new RuntimeException('RECIPE_ENV_PROD_BYPASS_MISSING');
if(!str_contains($router,"$"."portAllowed=$"."port===18513 || $"."mode==='isolated-fastcgi-v1'"))
 throw new RuntimeException('RECIPE_TEST_MODE_REGRESSION');
echo "EZS_GATEWAY_PROD_RECIPE_ISOLATION_CONTRACT_OK\n";
