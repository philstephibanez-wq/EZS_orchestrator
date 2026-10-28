<?php
declare(strict_types=1);
$s=(string)file_get_contents(__DIR__.'/../scripts/v2_lifecycle.ps1');
if(substr_count($s,"\$env:PHP_FCGI_MAX_REQUESTS = '0'")!==2) throw new RuntimeException('EZS_FCGI_UNLIMITED_NOT_APPLIED_TO_START_AND_REPAIR');
if(!str_contains($s,'EZS_DEV_REPAIR_FASTCGI_OK_CADDY_PRESERVED')) throw new RuntimeException('REPAIR_CONTRACT_MISSING');
echo "EZS_FASTCGI_REQUEST_LIMIT_CONTRACT_OK\n";
