<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/runtime_components/prod_gateway_php/router.php');
foreach(["SERVER_PORT","[18513,18515]","===8510","gateway_recipe_refused","is_file(\$testConfig)"] as $needle)
 if(!str_contains($s,$needle))throw new RuntimeException('RECIPE_GUARD_MISSING:'.$needle);
if(str_contains($s,"SERVER_NAME")||str_contains($s,"SERVER_ADDR"))throw new RuntimeException('RECIPE_GUARD_DEPENDS_ON_UNRELIABLE_SERVER_NAME');
echo "EZS_GATEWAY_FASTCGI_RECIPE_GUARD_OK\n";
