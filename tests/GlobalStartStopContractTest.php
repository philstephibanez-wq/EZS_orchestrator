<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$s=(string)file_get_contents($root.'/scripts/start.ps1');
$t=(string)file_get_contents($root.'/scripts/stop.ps1');
foreach ([$s,$t] as $code) {
    if (!str_contains($code,"[string]\$Target='all'")) throw new RuntimeException('GLOBAL_DEFAULT_MISSING');
    if (!str_contains($code,'v2_lifecycle.ps1')) throw new RuntimeException('DEV_LIFECYCLE_MISSING');
    if (!str_contains($code,'gateway-php.json')) throw new RuntimeException('PHP_GATEWAY_STATE_MISSING');
    if (str_contains($code,'python.exe')) throw new RuntimeException('PYTHON_REINTRODUCED');
}
if (!str_contains($s,'EZS_GLOBAL_START_READY') || !str_contains($s,'REFUSED_DEV_STALE_OR_PARTIAL_STATE') || !str_contains($s,'-Target gateway')) throw new RuntimeException('GLOBAL_START_INCOMPLETE');
if (!str_contains($t,'EZS_GLOBAL_STOP_OWNED_COMPONENTS_OK') || !str_contains($t,'REFUSED_UNOWNED_GATEWAY') || !str_contains($t,'-Target gateway')) throw new RuntimeException('GLOBAL_STOP_INCOMPLETE');
echo "EZS_GLOBAL_START_STOP_CONTRACT_OK\n";
