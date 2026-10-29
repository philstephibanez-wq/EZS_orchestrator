<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['EZS_PROD_REUSED_FOREIGN_PID_PRESERVED','EZS_PROD_REFUSED_SURVIVING_COMPONENT_','EZS_PROD_REFUSED_INVALID_SAVED_PID','if(Own $oldPid $entry.exe $entry.sig)','EZS_PROD_REFUSED_OCCUPIED_'] as $v){if(!str_contains($s,$v))throw new RuntimeException('MISSING:'.$v);}
echo "EZS_PROD_PID_REUSE_4_2C47_OK\n";
