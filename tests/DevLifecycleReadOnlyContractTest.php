<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/DevLifecycle.php';
use Ezs\Web\Module\Infrastructure\DevLifecycle;
$dir = sys_get_temp_dir().'/ezs-dev-lifecycle-test-'.bin2hex(random_bytes(6));
mkdir($dir.'/runtime/v2-dev', 0700, true);
try {
    $service = new DevLifecycle($dir);
    $s = $service->status();
    if ($s['state_present'] !== false || $s['lifecycle_authorized'] !== false) throw new RuntimeException('EMPTY_STATE_ACCEPTED');
    file_put_contents($dir.'/runtime/v2-dev/processes.json', json_encode(['php_pid'=>2123, 'caddy_pid'=>2124], JSON_THROW_ON_ERROR));
    $s = $service->status();
    if ($s['state_valid'] !== true || $s['identity_attested'] !== false) throw new RuntimeException('STATE_TRUSTED_AS_IDENTITY');
    foreach (['start', 'stop', 'repair', 'restart', 'status'] as $action) {
        if ($service->evaluate($action, ['verified'=>true, 'command_line_attested'=>true])['allowed'] !== false)
            throw new RuntimeException('UNVERIFIED_MUTATION_ALLOWED:'.$action);
    }
    file_put_contents($dir.'/runtime/v2-dev/processes.json', '{"php_pid":1,"caddy_pid":1}');
    if ($service->status()['state_valid'] !== false) throw new RuntimeException('DUPLICATED_PID_ACCEPTED');
    echo "EZS_DEV_LIFECYCLE_READ_ONLY_CONTRACT_OK\n";
} finally {
    @unlink($dir.'/runtime/v2-dev/processes.json');
    @rmdir($dir.'/runtime/v2-dev');
    @rmdir($dir.'/runtime');
    @rmdir($dir);
}
