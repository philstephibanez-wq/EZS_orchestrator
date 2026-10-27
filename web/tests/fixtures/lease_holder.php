<?php

declare(strict_types=1);

require_once dirname(__DIR__, 2) . '/src/Module/Coordination/ExclusiveLease.php';

use Ezs\Web\Module\Coordination\ExclusiveLease;

if ($argc !== 3) {
    exit(64);
}

$lease = new ExclusiveLease($argv[1], $argv[2]);
if (!$lease->acquire()) {
    exit(3);
}
// Readiness is issued only once the OS lock has been acquired.
echo "LEASE_READY\n";
flush();
sleep(30);
$lease->release();
