<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/Module/Infrastructure/EcosystemProcessEvidence.php';
require_once dirname(__DIR__) . '/src/Module/Infrastructure/WindowsProcessInventory.php';
require_once dirname(__DIR__) . '/src/Module/Infrastructure/EcosystemLifecycleGuard.php';
use Ezs\Web\Module\Infrastructure\{EcosystemLifecycleGuard,WindowsProcessInventory};
$root = sys_get_temp_dir() . '/ezs-unit-' . bin2hex(random_bytes(8));
mkdir($root . '/runtime/v2-dev', 0700, true);
mkdir($root . '/runtime/v2-prod', 0700, true);
$dev = $root . '/runtime/v2-dev/processes.json';
$prod = $root . '/runtime/v2-prod/processes.json';
file_put_contents($dev, '{"php_pid":12345,"caddy_pid":12346}');
file_put_contents($prod, '{"gateway_pid":98765}');
try {
    $guard = new EcosystemLifecycleGuard();
    $runs = 0;
    $inventory = new WindowsProcessInventory(static function () use (&$runs): iterable {
        ++$runs;
        return [];
    });
    $cleaned = $guard->cleanupDevStale($root, $inventory, static fn(int $port): bool => false);
    if ($cleaned !== 1 || $runs !== 2 || is_file($dev) || file_get_contents($prod) !== '{"gateway_pid":98765}') {
        throw new RuntimeException('DEV_ONLY_STALE_CLEANUP_FAILED');
    }
    file_put_contents($dev, '{"php_pid":12345}');
    $blocked = false;
    try {
        $guard->cleanupDevStale($root, new WindowsProcessInventory(static fn(): iterable => []), static fn(int $port): bool => $port === 8791);
    } catch (RuntimeException $e) { $blocked = str_contains($e->getMessage(), 'PORT_ACTIVE'); }
    if (!$blocked || !is_file($dev)) throw new RuntimeException('ACTIVE_DEV_NOT_PRESERVED');
    echo "EZS_TEST_002_OK\n";
} finally {
    foreach ([$dev,$prod,$root.'/runtime/v2-dev/lifecycle.lock'] as $file) if (is_file($file)) unlink($file);
    rmdir($root.'/runtime/v2-dev'); rmdir($root.'/runtime/v2-prod'); rmdir($root.'/runtime'); rmdir($root);
}
