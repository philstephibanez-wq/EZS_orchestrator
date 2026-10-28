<?php
declare(strict_types=1);
$root = dirname(__DIR__);
foreach (['scripts/start.ps1', 'scripts/stop.ps1', 'scripts/v2_lifecycle.ps1'] as $path) {
    if (is_file($root.'/'.$path)) {
        throw new RuntimeException('EZS_POWERSHELL_PURGE_INCOMPLETE:'.$path);
    }
}
require_once $root.'/src/Module/Infrastructure/DevLifecycle.php';
$service = new \Ezs\Web\Module\Infrastructure\DevLifecycle($root);
foreach (['start','stop','repair'] as $action) {
    if (($service->evaluate($action, [])['allowed'] ?? null) !== false) {
        throw new RuntimeException('EZS_LIFECYCLE_MUTATION_UNEXPECTEDLY_ENABLED:'.$action);
    }
}
echo "EZS_LEGACY_POWERSHELL_PURGE_CONTRACT_OK\n";
