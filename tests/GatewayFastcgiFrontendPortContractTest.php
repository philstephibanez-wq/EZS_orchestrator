<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/runtime_components/prod_gateway_php/router.php');
foreach(['[18513,18514,18515]','===8510','SERVER_PORT','gateway_recipe_refused'] as $token)
 if(!str_contains($s,$token))throw new RuntimeException('RECIPE_PORT_GUARD_MISSING:'.$token);
if(!str_contains($s,'frontend Caddy port (18514)'))throw new RuntimeException('FASTCGI_PORT_SEMANTICS_NOT_DOCUMENTED');
echo "EZS_GATEWAY_FASTCGI_FRONTEND_PORT_CONTRACT_OK\n";
