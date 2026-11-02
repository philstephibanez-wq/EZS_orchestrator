<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExpiredLeaseSweep;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PDO;
use PHPUnit\Framework\TestCase;

final class ExpiredLeaseSweepTest extends TestCase
{
    private string $directory;
    private string $database;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite unavailable');
        }
        $this->directory = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_sweep_'.bin2hex(random_bytes(12));
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

    public function testUnattestedGpuRemainsBlocked(): void
    {
        $store = new GlobalQueueStore($this->database);
        $store->enqueue('LAB','one','sweep-one','analysis','gpu');
        $running = $store->claim('gpu');
        $pdo = new PDO('sqlite:'.$this->database);
        $pdo->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.(int)$running['id']);
        $result = (new ExpiredLeaseSweep($store))->run(static fn (array $proof): bool => false);
        self::assertSame(['inspected'=>1,'recovered'=>0,'blocked'=>1,'stale'=>0,'errors'=>0], $result);
        self::assertSame('running', $store->byId((int)$running['id'])['state']);
        unset($pdo, $store);
    }

    public function testAttestedRecoveryFencesOldToken(): void
    {
        $store = new GlobalQueueStore($this->database);
        $store->enqueue('LAB','one','sweep-one','analysis','gpu');
        $running = $store->claim('gpu');
        $pdo = new PDO('sqlite:'.$this->database);
        $pdo->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.(int)$running['id']);
        $proofs = [];
        $result = (new ExpiredLeaseSweep($store))->run(static function (array $proof) use (&$proofs): bool {
            $proofs[] = $proof;
            return true;
        });
        self::assertSame(1, $result['recovered']);
        self::assertSame((int)$running['claim_generation'], $proofs[0]['claim_generation']);
        self::assertSame('queued', $store->byId((int)$running['id'])['state']);
        $this->expectException(\DomainException::class);
        $store->heartbeat((int)$running['id'], $running['lease_token']);
    }

    public function testInvalidLimitRejected(): void
    {
        $store = new GlobalQueueStore($this->database);
        $this->expectException(\InvalidArgumentException::class);
        (new ExpiredLeaseSweep($store))->run(static fn (array $proof): bool => false, 101);
    }
}
