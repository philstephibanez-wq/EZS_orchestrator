<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$version=trim((string)file_get_contents($r.'/VERSION'));
if($version!=='2.4b')throw new RuntimeException('STABLE_VERSION_NOT_2_4B');
$lifecycle=(string)file_get_contents($r.'/scripts/v2_lifecycle.ps1');
$lab=(string)file_get_contents($r.'/scripts/lab-assistant.ps1');
$stop=(string)file_get_contents($r.'/scripts/stop.ps1');
$start=(string)file_get_contents($r.'/scripts/start.ps1');
foreach (['EZS_STOP_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED','EZS_START_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED'] as $marker) {
    if(!str_contains($lifecycle,$marker))throw new RuntimeException('ORCHESTRATOR_LIFECYCLE_MISSING:'.$marker);
}
foreach (['EZS_LA_BACKENDS_STOP_OK_8701_8713_SHARED_CADDY_PRESERVED','EZS_LA_BACKENDS_ALREADY_RUNNING_VERIFIED'] as $marker) {
    if(!str_contains($lab,$marker))throw new RuntimeException('LAB_ASSISTANT_LIFECYCLE_MISSING:'.$marker);
}
if(!str_contains($stop,"'lab-assistant.ps1') -Action stop")||!str_contains($stop,"'v2_lifecycle.ps1') -Action stop"))throw new RuntimeException('GLOBAL_STOP_MISSING');
if(!str_contains($start,"'lab-assistant.ps1') -Action start"))throw new RuntimeException('GLOBAL_START_MISSING');
echo "EZS_LIFECYCLE_STABLE_2_4B_CONTRACT_OK\n";
