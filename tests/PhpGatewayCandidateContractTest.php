<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$candidate=(string)file_get_contents($root.'/runtime_components/prod_gateway_php/router.php');
$legacy=(string)file_get_contents($root.'/runtime_components/prod_gateway/server.py');
foreach(['/__ezscore_gateway_health','/__ezscore_gateway_status','ezscore.online-gateway.v3','/internal/media/auth','/internal/analysis/worker','/internal/analysis/desktop','X-Forwarded-Proto','X-Forwarded-Host','X-Forwarded-For','maintenancePage','Content-Length','php://input','fpassthru'] as $token){
 if(!str_contains($candidate,$token)||(!in_array($token,['maintenancePage','Content-Length','php://input','fpassthru'],true)&&!str_contains($legacy,$token)))
   throw new RuntimeException('GATEWAY_CANDIDATE_PARITY_MARKER_MISSING:'.$token);
}
if(str_contains($candidate,'shell_exec(')||str_contains($candidate,'powershell'))throw new RuntimeException('GATEWAY_EXTERNAL_SHELL_FORBIDDEN');
if(!is_file($root.'/runtime_components/prod_gateway/server.py'))throw new RuntimeException('ACTIVE_PYTHON_GATEWAY_REMOVED_PREMATURELY');
echo "EZS_PHP_GATEWAY_CANDIDATE_CONTRACT_OK\n";
