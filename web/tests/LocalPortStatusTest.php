<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/Module/Infrastructure/LocalPortStatus.php';
$probe = new \Ezs\Web\Module\Infrastructure\LocalPortStatus();
$items = $probe->snapshot();
if (count($items) !== 3) { throw new RuntimeException('unexpected_targets'); }
foreach ($items as $item) {
    if ($item['environment'] !== 'dev' || $item['port'] === 8501 || !is_bool($item['tcp_listening'])) {
        throw new RuntimeException('prod_or_invalid_probe');
    }
}
echo "LOCAL_LISTENERS_OK\n";
