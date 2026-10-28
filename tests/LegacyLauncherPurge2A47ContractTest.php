<?php
declare(strict_types=1);
$root=dirname(__DIR__);
foreach (['scripts/infrastructure_restore.ps1','launch.bat','stop.bat'] as $path) {
    if (is_file($root.'/'.$path)) throw new RuntimeException('LEGACY_LAUNCHER_REMAINING:'.$path);
}
if (is_file($root.'/runtime_components/prod_gateway/server.py')) throw new RuntimeException('PYTHON_GATEWAY_REINTRODUCED');
foreach (['scripts/start.ps1','scripts/stop.ps1','scripts/v2_lifecycle.ps1','scripts/prod_lifecycle.ps1',
    'runtime_components/prod_gateway_php/router.php','config/caddy/Caddyfile.gateway-php-candidate'] as $path) {
    if (!is_file($root.'/'.$path)) throw new RuntimeException('REQUIRED_MIGRATION_SOURCE_MISSING:'.$path);
}
$prod=(string)file_get_contents($root.'/scripts/prod_lifecycle.ps1');
if (!str_contains($prod,'runtime_components\\prod_gateway\\server.py')) {
    throw new RuntimeException('PROD_LEGACY_REFERENCE_UNEXPECTEDLY_CHANGED_REASSESS_GATE');
}
echo "EZS_LEGACY_GATEWAY_PURGE_RECONCILED_OK\n";
