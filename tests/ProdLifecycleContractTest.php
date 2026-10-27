<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$ps=(string)file_get_contents($root.'/scripts/prod_lifecycle.ps1');
foreach (['EZS_PROD_REFUSED_OCCUPIED_', 'EZS_PROD_REFUSED_UNVERIFIED_PROCESS_OWNERSHIP','EZS_PROD_STOP_INCOMPLETE_STATE_PRESERVED','SetMode $true','EZS_PROD_NORMAL_REFUSED_BACKEND_','EZS_PROD_START_MAINTENANCE_OK','EZS_PROD_STOP_VERIFIED_DEV_UNTOUCHED','Caddyfile.prod-internal-candidate','Caddyfile.prod','php-cgi.exe','gateway_pid'] as $needle) {
    if(!str_contains($ps,$needle))throw new RuntimeException('PROD_CONTRACT_MISSING:'.$needle);
}
$runner=(string)file_get_contents($root.'/scripts/infrastructure_restore.ps1');
foreach(['EZS_RESTORE_PREFLIGHT_OK','EZS_RESTORE_START_READY_PROD_IN_MAINTENANCE','EZS_RESTORE_REFUSED_DEV_STATE_NOT_OWNED','EZS_RESTORE_REFUSED_PROD_STATE_NOT_OWNED'] as $needle) {
    if(!str_contains($runner,$needle))throw new RuntimeException('RESTORE_CONTRACT_MISSING:'.$needle);
}
if(!is_file($root.'/runtime_components/prod_gateway/server.py'))throw new RuntimeException('PROD_GATEWAY_SOURCE_MISSING');
echo "EZS_PROD_LIFECYCLE_STATIC_CONTRACT_OK\n";
