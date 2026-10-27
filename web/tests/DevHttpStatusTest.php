<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/Module/Infrastructure/DevHttpStatus.php';
$targets = (new \Ezs\Web\Module\Infrastructure\DevHttpStatus())->snapshot();
if (count($targets) !== 4) throw new RuntimeException('targets');
foreach ($targets as $target) {
    if (in_array($target['port'], [8501, 8510, 8602, 8701], true)) throw new RuntimeException('prod_or_backend_probe');
    if (!is_bool($target['tcp_listening']) || !is_bool($target['http_reachable'])) throw new RuntimeException('types');
}
echo "DEV_HTTP_STATUS_OK\n";
