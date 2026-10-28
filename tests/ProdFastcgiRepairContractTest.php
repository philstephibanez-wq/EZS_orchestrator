<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(["'repair-fastcgi'","EZS_PROD_FASTCGI_REPAIR_REFUSED_OTHER_COMPONENTS_UNVERIFIED","EZS_PROD_FASTCGI_REPAIR_REFUSED_PROCESS_OR_PORT_PRESENT","EZS_PROD_FASTCGI_REPAIR_OK_OTHER_COMPONENTS_PRESERVED"] as $v){if(!str_contains($s,$v))throw new RuntimeException('MISSING_PROD_REPAIR_GUARD:'.$v);}
if(substr_count($s,"PHP_FCGI_MAX_REQUESTS='0'")!==2)throw new RuntimeException('PROD_FASTCGI_QUOTA_NOT_DISABLED_ON_BOTH_PATHS');
echo "EZS_PROD_FASTCGI_REPAIR_CONTRACT_OK\n";
