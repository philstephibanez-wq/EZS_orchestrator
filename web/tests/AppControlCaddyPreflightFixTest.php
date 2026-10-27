<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/app-control.ps1');
if(str_contains($s,'$LASTEXITCODE -ne 0'))throw new RuntimeException('stale LASTEXITCODE dependency');
foreach(['$caddy = @(& $CaddyCheck -Action status)','$caddy.Count -ne 1','$caddyText.Trim()','APP_CONTROL_SHARED_CADDY_UNAVAILABLE'] as $k)if(!str_contains($s,$k))throw new RuntimeException('missing '.$k);
if(!str_contains($s,'AssertOrchestrator'))throw new RuntimeException('orchestrator guard missing');
echo "EZS_APP_CONTROL_CADDY_PREFLIGHT_FIX_OK\n";
