<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/runtime_components/prod_gateway_php/router.php');
foreach(["'server_port'","'config_exists'","'script_matches'","'script_filename_present'","SCRIPT_FILENAME","realpath(__FILE__)","[18513,18514,18515]"] as $token)if(!str_contains($s,$token))throw new RuntimeException('RECIPE_DIAGNOSTIC_MISSING:'.$token);
if(str_contains($s,"'config_path'")||str_contains($s,"'env'"))throw new RuntimeException('RECIPE_DIAGNOSTIC_SENSITIVE_DATA');
echo "EZS_GATEWAY_RECIPE_DIAGNOSTIC_CONTRACT_OK\n";
