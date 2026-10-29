<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=(string)file_get_contents($r.'/scripts/start.ps1');
$prod=strpos($s,"if(\$ProdAction -ne ''){\n    Invoke-EzsProdLifecycle -Action \$ProdAction\n    return\n}");
$dev=strpos($s,'Invoke-EzsRootLifecycle -Action start');
if($prod===false||$dev===false||$prod>=$dev)throw new RuntimeException('PROD_ROUTING_AFTER_DEV');
if(strpos($s,"if(\$Action -eq 'status'){",$dev)!==false && $dev===0)throw new RuntimeException('UNEXPECTED');
if(!str_contains($s,"if(\$Action -eq 'start'){\n        if(\$null -ne \$s){throw 'EZS_PROD_REFUSED_EXISTING_STATE'}"))throw new RuntimeException('PROD_GUARD_REMOVED');
echo "EZS_PROD_ROUTING_4_2C35_OK\n";
