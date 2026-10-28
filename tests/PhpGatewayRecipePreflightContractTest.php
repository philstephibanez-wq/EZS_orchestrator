<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$router=(string)file_get_contents($root.'/runtime_components/prod_gateway_php/router.php');
$python=(string)file_get_contents($root.'/runtime_components/prod_gateway/server.py');
$cli=(string)file_get_contents($root.'/bin/gateway_recipe.php');
if(!str_contains($router,"header('Retry-After: 2')"))throw new RuntimeException('MISSING_INTERNAL_RETRY_AFTER');
if(!str_contains($router,'#101820')||!str_contains($python,'#101820'))throw new RuntimeException('MAINTENANCE_HTML_NOT_ALIGNED');
if(!str_contains($cli,'EZS_RECIPE_BACKEND_18511_UNAVAILABLE'))throw new RuntimeException('MISSING_BACKEND_PREFLIGHT');
echo "EZS_PHP_GATEWAY_RECIPE_PREFLIGHT_CONTRACT_OK\n";
