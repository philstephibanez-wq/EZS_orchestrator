<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
if(!str_contains($start,"-Action status 6>&1 | Out-String"))throw new RuntimeException('DEV_STATUS_INFORMATION_STREAM_NOT_CAPTURED');
if(!str_contains($start,"php_owned=True caddy_owned=True state_present=True"))throw new RuntimeException('HEALTHY_DEV_STATE_NOT_RECOGNIZED');
if(!str_contains($start,"EZS_GLOBAL_START_REFUSED_DEV_STALE_OR_PARTIAL_STATE"))throw new RuntimeException('STALE_DEV_GUARD_MISSING');
echo "EZS_GLOBAL_DEV_STATUS_CAPTURE_CONTRACT_OK\n";
