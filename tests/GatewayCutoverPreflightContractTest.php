<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$source=(string)file_get_contents($root.'/bin/gateway_cutover_preflight.php');
foreach(['READ_ONLY_NO_CUTOVER',"'can_cutover'=>false",'python_rollback','prod_gateway_protocol_valid','No exercised rollback procedure'] as $token) {
 if(!str_contains($source,$token))throw new RuntimeException('CUTOVER_PREFLIGHT_MISSING:'.$token);
}
if(str_contains($source,'Stop-Process')||str_contains($source,'proc_open('))throw new RuntimeException('CUTOVER_PREFLIGHT_MUTATING_ACTION');
echo "EZS_GATEWAY_CUTOVER_PREFLIGHT_CONTRACT_OK\n";
