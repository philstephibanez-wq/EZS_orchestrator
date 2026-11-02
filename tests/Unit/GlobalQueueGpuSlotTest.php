<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PDO;
use PHPUnit\Framework\TestCase;

final class GlobalQueueGpuSlotTest extends TestCase
{
    private string $directory;
    private string $database;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite unavailable');
        }
        $this->directory = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_gpu_'.bin2hex(random_bytes(12));
        if (!mkdir($this->directory, 0700)) {
            throw new \RuntimeException('test_directory_unavailable');
        }
        $this->database = $this->directory.DIRECTORY_SEPARATOR.'synthetic.sqlite';
    }

    protected function tearDown(): void
    {
        if (!isset($this->directory)) return;
        foreach (['synthetic.sqlite', 'synthetic.sqlite-wal', 'synthetic.sqlite-shm'] as $name) {
            $file = $this->directory.DIRECTORY_SEPARATOR.$name;
            if (is_file($file)) unlink($file);
        }
        if (is_dir($this->directory)) rmdir($this->directory);
    }

    public function testOnlyOneGpuRunningAcrossIndependentConnections(): void
    {
        $a = new GlobalQueueStore($this->database);
        $b = new GlobalQueueStore($this->database);
        $first = $a->enqueue('LAB','synthetic-1','gpu-key-1','analysis','gpu',50);
        $second = $a->enqueue('Assistant','synthetic-2','gpu-key-2','review','gpu',90);
        $cpu = $a->enqueue('LAB','synthetic-cpu','cpu-key','analysis','cpu',50);

        $running = $a->claim('gpu');
        self::assertSame((int)$second['id'], (int)$running['id']);
        self::assertNull($b->claim('gpu'));
        self::assertSame((int)$cpu['id'], (int)$b->claim('cpu')['id']);
        self::assertSame('queued', $b->byId((int)$first['id'])['state']);

        $a->finish((int)$running['id'], $running['lease_token'], true);
        self::assertSame((int)$first['id'], (int)$b->claim('gpu')['id']);
        unset($b, $a);
    }

    public function testExpiredRunningGpuStillBlocksUntilFencedRecovery(): void
    {
        $queue = new GlobalQueueStore($this->database);
        $queue->enqueue('LAB','synthetic-1','key-1','analysis','gpu');
        $queue->enqueue('LAB','synthetic-2','key-2','analysis','gpu');
        $running = $queue->claim('gpu');
        $db = new PDO('sqlite:'.$this->database);
        $db->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.(int)$running['id']);
        self::assertNull($queue->claim('gpu'));
        self::assertSame('running', $queue->byId((int)$running['id'])['state']);
        unset($db, $queue);
    }
}
