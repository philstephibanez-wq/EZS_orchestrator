<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PDO;
use PHPUnit\Framework\TestCase;

final class GlobalQueueSingleActiveFifo4_3A8Test extends TestCase
{
    private string $path;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite required');
        }
        $temp = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        self::assertDirectoryExists($temp);
        $this->path = $temp.'/ezs-fifo-'.bin2hex(random_bytes(12)).'.sqlite';
    }

    protected function tearDown(): void
    {
        if (!isset($this->path)) return;
        foreach ([$this->path, $this->path.'-wal', $this->path.'-shm'] as $file) {
            if (is_file($file)) @unlink($file);
        }
    }

    public function testOnlyOneActiveJobAcrossCpuAndGpu(): void
    {
        $store = new GlobalQueueStore($this->path);
        $store->enqueue('lab', 'analysis_job:100', 'fifo.100', 'profile', 'gpu');
        $store->enqueue('lab', 'analysis_job:101', 'fifo.101', 'profile', 'cpu');
        $first = $store->claim('gpu');
        self::assertIsArray($first);
        self::assertSame('analysis_job:100', $first['external_id']);
        self::assertNull($store->claim('cpu'));
        self::assertNull($store->claim('gpu'));
        $store->finish((int)$first['id'], (string)$first['lease_token'], false);
        $next = $store->claim('cpu');
        self::assertIsArray($next);
        self::assertSame('analysis_job:101', $next['external_id']);
    }

    public function testFirstInFirstOutIgnoresPriorityAndRejectsJumpingAhead(): void
    {
        $store = new GlobalQueueStore($this->path);
        $old = $store->enqueue('lab', 'analysis_job:200', 'fifo.200', 'profile', 'gpu', 10);
        $store->enqueue('lab', 'analysis_job:201', 'fifo.201', 'profile', 'gpu', 100);
        self::assertNull($store->claim('gpu', 120, (int)$old['id'] + 1));
        $first = $store->claim('gpu', 120, (int)$old['id']);
        self::assertIsArray($first);
        self::assertSame((int)$old['id'], (int)$first['id']);
        $store->finish((int)$first['id'], (string)$first['lease_token'], true);
        $second = $store->claim('gpu');
        self::assertIsArray($second);
        self::assertSame('analysis_job:201', $second['external_id']);
    }

    public function testHeadOfLineBlocksOtherResourceInsteadOfReordering(): void
    {
        $store = new GlobalQueueStore($this->path);
        $store->enqueue('lab', 'analysis_job:300', 'fifo.300', 'profile', 'cpu');
        $store->enqueue('lab', 'analysis_job:301', 'fifo.301', 'profile', 'gpu');
        self::assertNull($store->claim('gpu'));
        $first = $store->claim('cpu');
        self::assertIsArray($first);
        self::assertSame('analysis_job:300', $first['external_id']);
    }

    public function testExpiredRunningJobStillPreventsDoubleExecution(): void
    {
        $store = new GlobalQueueStore($this->path);
        $store->enqueue('lab', 'analysis_job:400', 'fifo.400', 'profile', 'gpu');
        $store->enqueue('lab', 'analysis_job:401', 'fifo.401', 'profile', 'gpu');
        $first = $store->claim('gpu');
        self::assertIsArray($first);
        $pdo = new PDO('sqlite:'.$this->path);
        $pdo->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.(int)$first['id']);
        self::assertNull($store->claim('gpu'));
        self::assertSame('running', $store->byId((int)$first['id'])['state']);
    }
}
