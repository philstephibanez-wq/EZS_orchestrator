<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$router=(string)file_get_contents($root.'/runtime_components/prod_gateway_php/router.php');
$runner=(string)file_get_contents($root.'/bin/gateway_fastcgi_autotest.php');
foreach(["EZS_GATEWAY_RECIPE_MODE","isolated-fastcgi-v1","configIsTemp","scriptAllowed","gateway_recipe_refused"] as $token)if(!str_contains($router,$token))throw new RuntimeException('RECIPE_GUARD_MISSING:'.$token);
if(!str_contains($runner,"['EZS_GATEWAY_RECIPE_MODE']='isolated-fastcgi-v1'"))throw new RuntimeException('RECIPE_MODE_NOT_INJECTED');
echo "EZS_GATEWAY_FASTCGI_EXPLICIT_MODE_CONTRACT_OK\n";
