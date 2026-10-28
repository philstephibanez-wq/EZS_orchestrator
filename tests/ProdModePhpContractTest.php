<?php
$root=dirname(__DIR__);
$service=(string)file_get_contents($root.'/src/Module/Infrastructure/ProdModeService.php');
$controller=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/ProdOperationsController.php');
if(!str_contains($controller,'$prodMode->apply($action)')) throw new RuntimeException('PROD_MODE_PHP_NOT_USED');
if(str_contains($controller,'powershell.exe')||str_contains($controller,'prod_lifecycle.ps1')) throw new RuntimeException('POWERSHELL_UI_REGRESSION');
foreach(['flock(', 'online-gateway.json','__ezscore_gateway_status','prod_backend_unavailable','rename('] as $needle) if(!str_contains($service,$needle)) throw new RuntimeException('PROD_MODE_GUARD_MISSING: '.$needle);
echo "EZS_PROD_MODE_PHP_CONTRACT_OK\n";
