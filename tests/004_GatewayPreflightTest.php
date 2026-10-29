<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/vendor/autoload.php';
use Ezs\Web\Module\Infrastructure\GatewayPreflightCommand;

$dir = sys_get_temp_dir() . '/ezs-gateway-preflight-test-' . bin2hex(random_bytes(6));
try {
    foreach (['config/caddy', 'runtime_components/prod_gateway_php', 'runtime_components/prod_gateway', 'runtime/v2-prod'] as $sub) {
        if (!mkdir($dir . '/' . $sub, 0777, true) && !is_dir($dir . '/' . $sub)) throw new RuntimeException('mkdir_failed');
    }
    file_put_contents($dir . '/config/caddy/Caddyfile.gateway-php-candidate', 'test');
    file_put_contents($dir . '/runtime_components/prod_gateway_php/router.php', '<?php');
    file_put_contents($dir . '/runtime_components/prod_gateway/server.py', 'pass');
    file_put_contents($dir . '/runtime/v2-prod/processes.json', '{}');

    $candidate = GatewayPreflightCommand::candidate($dir);
    if (!$candidate['success'] || $candidate['data']['prod_cutover_authorized'] !== false) throw new RuntimeException('candidate_readonly_failed');
    $valid = ['protocol'=>'ezscore.online-gateway.v3','ok'=>true,'backend_port'=>8511,'maintenance'=>true];
    $probe = static fn(string $uri): array => ['http'=>200, 'body'=>json_encode($valid, JSON_THROW_ON_ERROR)];
    $cutover = GatewayPreflightCommand::cutover($dir, $probe);
    if (!$cutover['success'] || $cutover['data']['can_cutover'] !== false || $cutover['data']['prod_maintenance'] !== true) throw new RuntimeException('cutover_readonly_failed');
    $failed = GatewayPreflightCommand::cutover($dir, static fn(string $uri): array => ['http'=>503, 'body'=>null]);
    if ($failed['success'] || $failed['data']['can_cutover'] !== false) throw new RuntimeException('cutover_failure_failed');
    echo "EZS_TEST_004_OK\n";
} finally {
    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($it as $file) $file->isDir() ? rmdir($file->getPathname()) : unlink($file->getPathname());
    if (is_dir($dir)) rmdir($dir);
}
