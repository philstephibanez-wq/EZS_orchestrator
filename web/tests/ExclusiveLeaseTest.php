<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/src/Module/Coordination/ExclusiveLease.php';

use Ezs\Web\Module\Coordination\ExclusiveLease;

$directory = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ezs_lease_test_' . bin2hex(random_bytes(8));
$first = new ExclusiveLease($directory, 'control');
$second = new ExclusiveLease($directory, 'control');
$gpu = new ExclusiveLease($directory, 'gpu-executor');
try {
    if (!$first->acquire()) {
        throw new RuntimeException('first_acquire_failed');
    }
    if ($second->acquire()) {
        throw new RuntimeException('double_owner_allowed');
    }
    if (!$gpu->acquire()) {
        throw new RuntimeException('independent_scope_blocked');
    }
    $first->release();
    if (!$second->acquire()) {
        throw new RuntimeException('lease_not_released');
    }
    echo "EXCLUSIVE_LEASE_OK\n";
} finally {
    $first->release();
    $second->release();
    $gpu->release();
    foreach (['control', 'gpu-executor'] as $scope) {
        @unlink($directory . DIRECTORY_SEPARATOR . $scope . '.lock');
    }
    @rmdir($directory);
}
