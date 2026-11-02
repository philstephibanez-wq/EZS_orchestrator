<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PDO;
use PHPUnit\Framework\TestCase;

final class GlobalQueueRecoveryTest extends TestCase
{
    private string $directory;
    private string $database;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite unavailable');
        $this->directory = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_recovery_'.bin2hex(random_bytes(12));
        if (!mkdir($this->directory, 0700)) throw new \RuntimeException('synthetic_directory_unavailable');
        $this->database = $this->directory.DIRECTORY_SEPARATOR.'synthetic.sqlite';
    }

    protected function tearDown(): void
    {
        if (!isset($this->directory)) return;
        foreach (['synthetic.sqlite', 'synthetic.sqlite-wal', 'synthetic.sqlite-shm'] as $file) {
            $path = $this->directory.DIRECTORY_SEPARATOR.$file;
            if (is_file($path)) unlink($path);
        }
        if (is_dir($this->directory)) rmdir($this->directory);
    }

    private function expire(int $id): void
    {
        $pdo = new PDO('sqlite:'.$this->database);
        $pdo->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.$id);
    }

    public function testExpiredGpuNeedsProofBeforeRetryAndOldTokenIsFenced(): void
    {
        $a = new GlobalQueueStore($this->database);
        $b = new GlobalQueueStore($this->database);
        $a->enqueue('LAB','song-1','one','analysis','gpu');
        $a->enqueue('LAB','song-2','two','analysis','gpu');
        $running = $a->claim('gpu');
        $id = (int)$running['id'];
        $generation = (int)$running['claim_generation'];
        $token = $running['lease_token'];
        $this->expire($id);
        self::assertCount(1, $b->expiredLeases());
        self::assertArrayNotHasKey('lease_token', $b->expiredLeases()[0]);
        self::assertNull($b->claim('gpu'));
        try {
            $b->recoverExpired($id, $generation, static fn(array $proof): bool => false);
            self::fail('Attestation rejected was accepted');
        } catch (\DomainException $e) {
            self::assertSame('executor_not_attested_stopped', $e->getMessage());
        }
        self::assertSame('running', $a->byId($id)['state']);
        $proofSeen = false;
        $recovered = $b->recoverExpired($id, $generation, function (array $proof) use (&$proofSeen, $generation, $id): bool {
            $proofSeen = (int)$proof['id'] === $id && $proof['claim_generation'] === $generation;
            return $proofSeen;
        });
        self::assertTrue($proofSeen);
        self::assertSame('queued', $recovered['state']);
        self::assertSame($generation + 1, (int)$recovered['claim_generation']);
        try {
            $a->heartbeat($id, $token);
            self::fail('Old token heartbeat was accepted');
        } catch (\DomainException $e) {
            self::assertSame('lease_not_current', $e->getMessage());
        }
        try {
            $a->finish($id, $token, true);
            self::fail('Old token finish was accepted');
        } catch (\DomainException $e) {
            self::assertSame('lease_not_current', $e->getMessage());
        }
        self::assertNotNull($a->claim('gpu'));
        self::assertCount(1, $b->events('LAB'));
        unset($a, $b);
    }

    public function testStaleAttestationCannotResetRenewedLease(): void
    {
        $a = new GlobalQueueStore($this->database);
        $b = new GlobalQueueStore($this->database);
        $a->enqueue('LAB','song','key','analysis','gpu');
        $claimed = $a->claim('gpu');
        $id = (int)$claimed['id'];
        $generation = (int)$claimed['claim_generation'];
        $this->expire($id);
        try {
            $b->recoverExpired($id, $generation, function (array $proof) use ($a, $id, $claimed): bool {
                $a->heartbeat($id, $claimed['lease_token']); // expired: must reject
                return true;
            });
            self::fail('Expired heartbeat accepted');
        } catch (\DomainException $e) {
            self::assertSame('lease_not_current', $e->getMessage());
        }
        self::assertSame('running', $b->byId($id)['state']);
        try {
            $b->recoverExpired($id, $generation + 1, static fn(array $proof): bool => true);
            self::fail('Stale generation was accepted');
        } catch (\DomainException $e) {
            self::assertSame('lease_not_expired_current', $e->getMessage());
        }
        unset($a, $b);
    }
}
