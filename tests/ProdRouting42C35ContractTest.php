<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=(string)file_get_contents($r.'/scripts/start.ps1');
$dispatch="if(\$ProdAction -ne ''){\n    Invoke-EzsProdLifecycle -Action \$ProdAction\n    return\n}\nInvoke-EzsRootLifecycle -Action start";
if(substr_count($s,$dispatch)!==1)throw new RuntimeException('PROD_ROUTING_NOT_AT_ENTRY');
if(!str_contains($s,"if(\$Action -eq 'start'){\n        if(\$null -ne \$s){throw 'EZS_PROD_REFUSED_EXISTING_STATE'}"))throw new RuntimeException('PROD_GUARD_REMOVED');
if(!str_contains($s,"if(\$Action -eq 'status'){\n        \$ready=\$false"))throw new RuntimeException('PROD_STATUS_REMOVED');
echo "EZS_PROD_ROUTING_4_2C35_OK\n";
