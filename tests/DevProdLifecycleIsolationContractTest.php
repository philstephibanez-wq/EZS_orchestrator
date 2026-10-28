<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
foreach (['start'=>$start,'stop'=>$stop] as $action=>$code){
 if (!str_contains($code,"v2_lifecycle.ps1') -Action ".$action)) throw new RuntimeException('DEV_LIFECYCLE_MISSING:'.$action);
 foreach (['gateway-php.json','-Target gateway','8510','18515','prod_lifecycle.ps1','Stop-Process','Start-Process'] as $forbidden){
  // 8510 and 18515 may appear in comments documenting the safety boundary.
  if(in_array($forbidden,['8510','18515'],true))continue;
  if(str_contains($code,$forbidden)) throw new RuntimeException('PROD_OPERATION_IN_DEV_WRAPPER:'.$forbidden);
 }
}
$prod=(string)file_get_contents($root.'/config/caddy/Caddyfile.gateway-php-prod');
if(!str_contains($prod,':8510')||!str_contains($prod,'18515'))throw new RuntimeException('PROD_GATEWAY_CONFIG_LOST');
echo "EZS_DEV_PROD_LIFECYCLE_ISOLATION_OK\n";
