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
foreach (['Refuse-OtherDevListeners $c', '@(8502, 8852)', 'OwningProcess -ne $caddyPid', '@(8602, 8701, 8702, 8712, 8862)'] as $marker) {
    if (!str_contains($source, $marker)) throw new RuntimeException('CADDY_DEV_FACADE_GUARD_MISSING:' . $marker);
}
foreach (['EZS_FASTCGI_DIAGNOSTIC', 'EZS_FASTCGI_STDERR', 'EZS_START_FASTCGI_FAILED_DIAGNOSTIC_AVAILABLE', 'RedirectStandardError', 'RedirectStandardOutput'] as $marker) {
    if (!str_contains($source, $marker)) throw new RuntimeException('FASTCGI_DIAGNOSTIC_MISSING:' . $marker);
}
$start = strpos($source, 'function Wait-Port(');
$end = strpos($source, 'function Refuse-OtherDevListeners(', $start);
if ($start === false || $end === false) throw new RuntimeException('WAIT_PORT_FUNCTION_NOT_FOUND');
$waitPort = substr($source, $start, $end - $start);
if (str_contains($waitPort, 'if ((@(Listening $port)).Count -gt 0) { return $false }')
    || !str_contains($waitPort, 'if (Port-Owned $port $processId) { return $true }')
    || !str_contains($waitPort, 'if ($null -eq $live) { return $false }')
    || !str_contains($waitPort, 'return (Port-Owned $port $processId)')) {
    throw new RuntimeException('WAIT_PORT_EARLY_REJECTION_REGRESSION');
}
foreach (['EZS_DEV_REPAIR_REFUSED_CADDY_NOT_VERIFIED','EZS_DEV_REPAIR_REFUSED_PHP_PROCESS_OR_PORT_PRESENT','EZS_DEV_REPAIR_FASTCGI_OK_CADDY_PRESERVED','Port-Owned 8502 $caddyPid','Port-Owned 8852 $caddyPid'] as $marker) {
    if (!str_contains($source,$marker)) throw new RuntimeException('DEV_REPAIR_GUARD_MISSING:'.$marker);
}
$restore=(string)file_get_contents($root.'/scripts/infrastructure_restore.ps1');
if (!str_contains($restore,'& $dev -Action repair')) throw new RuntimeException('RESTORE_REPAIR_NOT_CONNECTED');
echo "EZS_V2_LIFECYCLE_STATIC_CONTRACT_OK\n";
