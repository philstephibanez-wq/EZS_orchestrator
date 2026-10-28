<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
$caddy=(string)file_get_contents($root.'/config/caddy/Caddyfile.gateway-php-prod');
foreach (['gateway','18515','8510','EZS_GATEWAY_PHP_PROD_8510_READY','Caddyfile.gateway-php-prod','v2_lifecycle.ps1'] as $token){
    if(!str_contains($start,$token))throw new RuntimeException('GATEWAY_START_MISSING:'.$token);
}
foreach (['gateway-php.json','STOP_REFUSED_UNVERIFIED_IDENTITY','18515','8510','v2_lifecycle.ps1'] as $token){
    if(!str_contains($stop,$token))throw new RuntimeException('GATEWAY_STOP_MISSING:'.$token);
}
if(!str_contains($caddy,'bind 127.0.0.1')||!str_contains($caddy,':8510')||!str_contains($caddy,'18515')
||!str_contains($caddy,'X-EZS-Original-URI'))throw new RuntimeException('GATEWAY_CONFIG_INVALID');
if(str_contains($start,'python.exe')||str_contains($stop,'python.exe'))throw new RuntimeException('PYTHON_REINTRODUCED');
echo "EZS_GATEWAY_PHP_PROD_BOOTSTRAP_CONTRACT_OK\n";
