<?php
declare(strict_types=1);
$root=dirname(__DIR__);
foreach (['scripts/infrastructure_restore.ps1','launch.bat','stop.bat'] as $path) {
    if (is_file($root.'/'.$path)) throw new RuntimeException('LEGACY_LAUNCHER_REMAINING:'.$path);
}
foreach (['runtime_components/prod_gateway/server.py','scripts/prod_lifecycle.ps1'] as $path) {
    if (!is_file($root.'/'.$path)) throw new RuntimeException('ACTIVE_PROD_SOURCE_PREMATURELY_REMOVED:'.$path);
}
$prod=(string)file_get_contents($root.'/scripts/prod_lifecycle.ps1');
if (!str_contains($prod,'runtime_components\\prod_gateway\\server.py')
    || !str_contains($prod, 'python.exe')) {
    throw new RuntimeException('PROD_LEGACY_CONTRACT_CHANGED');
}
echo "EZS_LEGACY_LAUNCHER_PURGE_2_A47_OK\n";
