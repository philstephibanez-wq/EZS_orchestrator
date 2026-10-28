<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/bin/gateway_autotest.php');
if(str_contains($s,'fclose($pipes[0])'))throw new RuntimeException('INVALID_FILE_DESCRIPTOR_CLOSE');
if(!str_contains($s,"!str_contains(\$out,'EZS_PHP_GATEWAY_RECIPE_PARITY_OK')"))throw new RuntimeException('MISSING_PARITY_SUCCESS_GUARD');
if(!str_contains($s,"EZS_RECIPE_CREATED_PROCESSES_CLEANED_UP"))throw new RuntimeException('MISSING_CLEANUP');
echo "EZS_GATEWAY_AUTOTEST_FILE_DESCRIPTOR_CONTRACT_OK\n";
