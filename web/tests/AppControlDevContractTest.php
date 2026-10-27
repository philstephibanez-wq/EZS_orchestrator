<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/app-control.ps1');
foreach(['AssertOrchestrator','APP_CONTROL_ORCHESTRATOR_BACKEND_MISSING','APP_CONTROL_SHARED_CADDY_UNAVAILABLE','-Action stop','-Action start','APP_CONTROL_OK'] as $k){if(!str_contains($s,$k))throw new RuntimeException('missing '.$k);}
if(str_contains($s,'Stop-Process')||str_contains($s,'Start-Process')||str_contains($s,'caddy.exe'))throw new RuntimeException('central coordinator must delegate not create process');
if(!str_contains($s,"ValidateSet('ezscore-dev')"))throw new RuntimeException('out of scope');
echo "EZS_APP_CONTROL_DEV_CONTRACT_OK\n";
