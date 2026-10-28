<?php
declare(strict_types=1);
$root=dirname(__DIR__);
foreach (['scripts/start.ps1','scripts/stop.ps1','scripts/start.ps1'] as $path) {
    if (!is_file($root.'/'.$path)) throw new RuntimeException('EZS_ESSENTIAL_LIFECYCLE_MISSING:'.$path);
}
$lifecycle=(string)file_get_contents($root.'/scripts/start.ps1');
foreach (["'start'","'stop'","'repair'","'status'"] as $action) {
    if (!str_contains($lifecycle,$action)) throw new RuntimeException('EZS_ESSENTIAL_ACTION_MISSING:'.$action);
}
foreach (['scripts/infrastructure_restore.ps1','launch.bat','stop.bat'] as $path) {
    if (is_file($root.'/'.$path)) throw new RuntimeException('EZS_ORPHAN_LAUNCHER_REINTRODUCED:'.$path);
}
require_once $root.'/src/Module/Infrastructure/DevLifecycle.php';
$service=new \Ezs\Web\Module\Infrastructure\DevLifecycle($root);
foreach (['start','stop','repair'] as $action) {
    if (($service->evaluate($action,[])['allowed']??null)!==false) throw new RuntimeException('EZS_UNVERIFIED_SYMFONY_MUTATION:'.$action);
}
echo "EZS_ESSENTIAL_LIFECYCLE_PRESERVED_OK\n";
