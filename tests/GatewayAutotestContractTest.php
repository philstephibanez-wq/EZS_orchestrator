<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/bin/gateway_autotest.php');
foreach(['EZS_RECIPE_PORT_OCCUPIED_',"'compare'",'proc_terminate($process)','array_reverse($jobs)','EZS_GATEWAY_AUTOTEST_OK','EZS_RECIPE_CREATED_PROCESSES_CLEANED_UP'] as $k)
 if(!str_contains($s,$k))throw new RuntimeException('AUTOTEST_CONTRACT_MISSING: '.$k);
if(str_contains($s,'taskkill')||str_contains($s,'Stop-Process'))throw new RuntimeException('UNSAFE_TERMINATION');
echo "EZS_GATEWAY_AUTOTEST_CONTRACT_OK\n";
