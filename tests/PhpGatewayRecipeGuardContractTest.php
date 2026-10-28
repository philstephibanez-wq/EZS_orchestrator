<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/runtime_components/prod_gateway_php/router.php');
if(str_contains($s,"SERVER_ADDR"))throw new RuntimeException('UNRELIABLE_SERVER_ADDR_GUARD');
foreach(["SERVER_NAME","SERVER_PORT","===8510","gateway_recipe_refused","is_file(\$testConfig)"] as $p){
 if(!str_contains($s,$p))throw new RuntimeException('MISSING_RECIPE_GUARD:'.$p);
}
echo "EZS_PHP_GATEWAY_RECIPE_GUARD_OK\n";
