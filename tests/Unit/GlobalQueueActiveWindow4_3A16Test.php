<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueActiveWindow;
use Ezs\Web\Module\Coordination\GlobalQueueLocation;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

final class GlobalQueueActiveWindow4_3A16Test extends TestCase
{
    public function testSyntheticQueueCannotInheritMainCutover(): void
    {
        $folder = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $path = tempnam($folder, 'ezs-window-');
        self::assertIsString($path);
        $before = getenv('EZS_QUEUE_ACTIVE_FROM_ID');
        try {
            putenv('EZS_QUEUE_ACTIVE_FROM_ID=999');
            self::assertSame(1, GlobalQueueActiveWindow::floor($path));
            $store = new GlobalQueueStore($path);
            $job = $store->enqueue('lab', 'analysis_job:1', 'window.1', 'profile', 'gpu');
            self::assertIsArray($store->claim('gpu', 120, (int)$job['id']));
        } finally {
            if ($before === false) putenv('EZS_QUEUE_ACTIVE_FROM_ID');
            else putenv('EZS_QUEUE_ACTIVE_FROM_ID='.$before);
            foreach ([$path, $path.'-wal', $path.'-shm'] as $file) if (is_file($file)) @unlink($file);
        }
    }

    public function testOnlyAnExplicitCanonicalQueueMayBeFiltered(): void
    {
        self::assertSame(1, GlobalQueueActiveWindow::floor(__FILE__));
    }
}
