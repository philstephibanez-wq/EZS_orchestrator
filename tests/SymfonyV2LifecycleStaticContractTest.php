<?php
declare(strict_types=1);
$root = dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
$source=(string)file_get_contents($root.'/scripts/v2_lifecycle.ps1');
if (!str_contains($start, "v2_lifecycle.ps1") || !str_contains($stop,"v2_lifecycle.ps1")) {
    throw new RuntimeException('CANONICAL_START_STOP_NOT_CONNECTED');
}
foreach (['EZS_LIFECYCLE_CONCURRENT_OPERATION','EZS_STOP_REFUSED_UNVERIFIED_PROCESS_OWNERSHIP','EZS_GLOBAL_STOP_REQUIRES_DEV_OWNERSHIP_PORT_','EZS_START_REFUSED_PORT_8790_OR_8791_IN_USE','Caddyfile.dev-root-candidate','-WindowStyle Hidden','PROD_UNTOUCHED'] as $token) {
    if (!str_contains($source,$token)) throw new RuntimeException('LIFECYCLE_GUARD_MISSING:'.$token);
}
echo "EZS_V2_LIFECYCLE_STATIC_CONTRACT_OK\n";
