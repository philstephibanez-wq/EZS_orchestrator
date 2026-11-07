<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PDO;
use PHPUnit\Framework\TestCase;

final class GlobalQueueNoExpiry4_3A18Test extends TestCase
{
    private string $path;

    protected function setUp(): void
    {
        $this->path = sys_get_temp_dir().'/ezs_queue_noexpiry_'.bin2hex(random_bytes(8)).'.sqlite';
    }

    protected function tearDown(): void
    {
        foreach (['', '-wal', '-shm'] as $suffix) @unlink($this->path.$suffix);
    }

    public function testClaimHasNoDeadlineAndRemainsExclusive(): void
    {
        $store = new GlobalQueueStore($this->path);
        $first = $store->enqueue('lab', 'analysis_job:204', 'test.noexpiry.204', 'profile', 'gpu');
        $store->enqueue('lab', 'analysis_job:205', 'test.noexpiry.205', 'profile', 'gpu');
        $claim = $store->claim('gpu', 30, (int)$first['id']);
        self::assertIsArray($claim);
        self::assertNull($claim['lease_until']);
        self::assertNull($store->claim('gpu', 30));
        $token = (string)$claim['lease_token'];
        $db = new PDO('sqlite:'.$this->path);
        // Simulate an old historical claim with a long-past deadline.
        $db->exec('UPDATE global_queue_jobs SET lease_until=1 WHERE id='.(int)$claim['id']);
        $event = $store->heartbeat((int)$claim['id'], $token, 30, 25);
        self::assertNull($event['lease_until']);
        self::assertSame('completed', $store->finish((int)$claim['id'], $token, true)['state']);
        $next = $store->claim('gpu', 30);
        self::assertNotNull($next);
        self::assertSame('analysis_job:205', $next['external_id']);
    }

    public function testStoppedRecoveryRequiresProofAndKeepsGenerationFence(): void
    {
        $store = new GlobalQueueStore($this->path);
        $row = $store->enqueue('lab', 'analysis_job:204', 'test.recover.204', 'profile', 'gpu');
        $claim = $store->claim('gpu', 30, (int)$row['id']);
        self::assertNotNull($claim);
        $generation = (int)$claim['claim_generation'];
        $oldToken = (string)$claim['lease_token'];
        try {
            $store->recoverStopped((int)$row['id'], $generation, static fn(array $proof): bool => false);
            self::fail('Missing attestation should have been refused');
        } catch (\DomainException $e) {
            self::assertSame('executor_not_attested_stopped', $e->getMessage());
        }
        self::assertSame('running', $store->byId((int)$row['id'])['state']);
        $reset = $store->recoverStopped((int)$row['id'], $generation, static fn(array $proof): bool => $proof['external_id'] === 'analysis_job:204');
        self::assertSame('queued', $reset['state']);
        self::assertSame($generation + 1, (int)$reset['claim_generation']);
        $new = $store->claim('gpu', 30, (int)$row['id']);
        self::assertNotNull($new);
        $this->expectException(\DomainException::class);
        $store->finish((int)$row['id'], $oldToken, true);
    }
}
