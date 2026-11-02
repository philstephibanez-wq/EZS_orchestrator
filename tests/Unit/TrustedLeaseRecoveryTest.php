<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\{ExecutorOwnershipRegistry,ExpiredLeaseSweep,GlobalQueueStore,TrustedLeaseRecovery};
use PDO;
use PHPUnit\Framework\TestCase;

final class TrustedLeaseRecoveryTest extends TestCase
{
    private string $dir;
    private string $database;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite unavailable');
        $this->dir = sys_get_temp_dir().DIRECTORY_SEPARATOR.'trusted_recovery_'.bin2hex(random_bytes(10));
        if (!mkdir($this->dir, 0700)) throw new \RuntimeException('test_directory_unavailable');
        $this->database = $this->dir.'/queue.sqlite';
    }

    protected function tearDown(): void
    {
        if (!isset($this->dir)) return;
        foreach (glob($this->dir.'/*') ?: [] as $file) unlink($file);
        rmdir($this->dir);
    }

    private function expire(int $id): void
    {
        (new PDO('sqlite:'.$this->database))->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.$id);
    }

    public function testMissingOwnershipIsNeverReclaimedEvenIfProbeWouldApprove(): void
    {
        $store = new GlobalQueueStore($this->database);
        $store->enqueue('LAB', 'one', 'one', 'analysis', 'gpu');
        $job = $store->claim('gpu');
        $this->expire((int)$job['id']);
        $probeCalls = 0;
        $recovery = new TrustedLeaseRecovery(
            new ExpiredLeaseSweep($store),
            new ExecutorOwnershipRegistry($this->database),
            static function (array $owner) use (&$probeCalls): array { ++$probeCalls; return ['status'=>'stopped_confirmed']; },
        );
        $outcome = $recovery->run();
        self::assertSame(1, $outcome['blocked']);
        self::assertSame(0, $outcome['recovered']);
        self::assertSame(0, $probeCalls);
        self::assertSame('running', $store->byId((int)$job['id'])['state']);
    }

    public function testRecordedOwnershipRequiresMatchingIndependentObservation(): void
    {
        $store = new GlobalQueueStore($this->database);
        $store->enqueue('LAB', 'two', 'two', 'analysis', 'gpu');
        $job = $store->claim('gpu');
        $id = (int)$job['id'];
        $registry = new ExecutorOwnershipRegistry($this->database);
        $registry->register($id, (int)$job['claim_generation'], $job['lease_token'], 'MAIN', 1234, '2026-11-02T07:00:00Z', 'launch-1');
        $this->expire($id);
        $probe = static fn (array $owner): array => ['status'=>'stopped_confirmed', 'node'=>$owner['node'], 'pid'=>$owner['pid'], 'created_at'=>$owner['created_at'], 'instance_id'=>$owner['instance_id']];
        $wrong = new TrustedLeaseRecovery(new ExpiredLeaseSweep($store), $registry, static function (array $owner) use ($probe): array {
            $observation = $probe($owner);
            $observation['instance_id'] = 'different-launch';
            return $observation;
        });
        self::assertSame(1, $wrong->run()['blocked']);
        self::assertSame('running', $store->byId($id)['state']);
        $trusted = new TrustedLeaseRecovery(new ExpiredLeaseSweep($store), $registry, $probe);
        self::assertSame(1, $trusted->run()['recovered']);
        self::assertSame('queued', $store->byId($id)['state']);
        $this->expectExceptionMessage('lease_not_current');
        $store->finish($id, $job['lease_token'], true);
    }
}
