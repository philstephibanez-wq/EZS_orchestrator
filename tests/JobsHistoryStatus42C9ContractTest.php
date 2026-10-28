<?php
declare(strict_types=1);

$root = dirname(__DIR__);
if (trim((string) file_get_contents($root . '/VERSION')) !== '4.2c9') {
    throw new RuntimeException('VERSION');
}
require $root . '/src/Module/Coordination/LegacyJobHistoryReader.php';

use Ezs\Web\Module\Coordination\LegacyJobHistoryReader;

$dir = sys_get_temp_dir() . '/ezs_recent_42c9_' . bin2hex(random_bytes(8));
$base = $dir . '/runtime/jobs';
$files = [];

try {
    for ($i = 1; $i <= 60; $i++) {
        $target = $i % 2 === 0 ? 'lab' : 'dev';
        $path = $base . '/' . $target . '/' . $i . '/run-1/result.json';
        if (!is_dir(dirname($path)) && !mkdir(dirname($path), 0700, true) && !is_dir(dirname($path))) {
            throw new RuntimeException('MKDIR');
        }
        $state = $i % 3 === 0 ? 'failed' : 'completed';
        file_put_contents($path, json_encode(['job_id' => $i, 'state' => $state, 'kind' => 'profile']));
        touch($path, 1700000000 + $i);
        $files[] = $path;
    }
    $reader = new LegacyJobHistoryReader($dir);
    $rows = $reader->recent(5);
    if (count($rows) !== 5 || $rows[0]['job_id'] !== 60 || $rows[4]['job_id'] !== 56) {
        throw new RuntimeException('LATEST_ORDER');
    }
    if ($reader->recent(100)[0]['job_id'] !== 60) {
        throw new RuntimeException('LARGE_LIMIT');
    }
    foreach ($files as $path) {
        if (!is_file($path)) {
            throw new RuntimeException('UNEXPECTED_MUTATION');
        }
    }
    $twig = (string) file_get_contents($root . '/templates/jobs/index.html.twig');
    foreach (['text-bg-success', 'text-bg-danger', 'text-bg-warning', 'text-bg-primary', 'text-bg-secondary'] as $marker) {
        if (!str_contains($twig, $marker)) {
            throw new RuntimeException('STATUS_COLOR_MISSING:' . $marker);
        }
    }
    echo "EZS_JOBS_HISTORY_STATUS_4_2C9_OK\n";
} finally {
    foreach ($files as $path) {
        @unlink($path);
        @rmdir(dirname($path));
        @rmdir(dirname(dirname($path)));
    }
    foreach (['dev', 'lab', 'prod'] as $target) {
        @rmdir($base . '/' . $target);
    }
    @rmdir($base);
    @rmdir(dirname($base));
    @rmdir(dirname(dirname($base)));
    @rmdir($dir);
}
