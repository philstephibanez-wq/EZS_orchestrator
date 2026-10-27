<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/src/Module/Coordination/ExclusiveLease.php';

use Ezs\Web\Module\Coordination\ExclusiveLease;

$directory = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ezs_lease_crash_' . bin2hex(random_bytes(8));
if (!mkdir($directory, 0700, true)) {
    throw new RuntimeException('temp_dir_failed');
}
$childScript = __DIR__ . '/fixtures/lease_holder.php';
$stdout = $directory . DIRECTORY_SEPARATOR . 'holder.stdout';
$stderr = $directory . DIRECTORY_SEPARATOR . 'holder.stderr';
$proc = null;
try {
    foreach (['control', 'gpu-executor'] as $scope) {
        // Windows-safe: array command means no shell-quoting ambiguity.
        $proc = proc_open(
            [PHP_BINARY, $childScript, $directory, $scope],
            [0 => ['pipe', 'r'], 1 => ['file', $stdout, 'w'], 2 => ['file', $stderr, 'w']],
            $pipes
        );
        if (!is_resource($proc)) {
            throw new RuntimeException('holder_start_failed');
        }
        fclose($pipes[0]);
        $ready = false;
        $deadline = microtime(true) + 6.0;
        do {
            clearstatcache(true, $stdout);
            if (is_file($stdout) && str_contains((string)file_get_contents($stdout), 'LEASE_READY')) {
                $ready = true;
                break;
            }
            usleep(50_000);
        } while (microtime(true) < $deadline);
        if (!$ready) {
            throw new RuntimeException('holder_never_ready: ' . (string)@file_get_contents($stderr));
        }
        $contender = new ExclusiveLease($directory, $scope);
        if ($contender->acquire()) {
            $contender->release();
            throw new RuntimeException('concurrent_owner_allowed: ' . $scope);
        }
        // This is deliberately an abnormal termination, not release().
        if (!proc_terminate($proc)) {
            throw new RuntimeException('holder_terminate_failed');
        }
        $status = proc_get_status($proc);
        $deadline = microtime(true) + 6.0;
        while ($status['running'] && microtime(true) < $deadline) {
            usleep(50_000);
            $status = proc_get_status($proc);
        }
        if ($status['running']) {
            throw new RuntimeException('holder_still_running');
        }
        proc_close($proc);
        $proc = null;
        $recovered = new ExclusiveLease($directory, $scope);
        if (!$recovered->acquire()) {
            throw new RuntimeException('lock_not_recovered_after_kill: ' . $scope);
        }
        $recovered->release();
    }
    echo "EXCLUSIVE_LEASE_CRASH_OK\n";
} finally {
    if (is_resource($proc)) {
        @proc_terminate($proc);
        @proc_close($proc);
    }
    foreach (['control', 'gpu-executor'] as $scope) {
        @unlink($directory . DIRECTORY_SEPARATOR . $scope . '.lock');
    }
    @unlink($stdout);
    @unlink($stderr);
    @rmdir($directory);
}
