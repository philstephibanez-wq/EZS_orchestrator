<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Coordination;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

/** Stateless acceptance tests for the current canonical queue, before Messenger activation. */
final class GlobalQueueMigrationContractTest extends TestCase
{
    private string $directory;
    private GlobalQueueStore $queue;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite is required for the canonical queue contracts');
        }
        $this->directory = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'ezs-queue-test-' . bin2hex(random_bytes(8));
        self::assertTrue(mkdir($this->directory, 0700, true));
        $this->queue = new GlobalQueueStore($this->directory . DIRECTORY_SEPARATOR . 'queue.sqlite');
    }

    protected function tearDown(): void
    {
        if (!isset($this->directory) || !is_dir($this->directory)) {
            return;
        }
        unset($this->queue);
        foreach (glob($this->directory . DIRECTORY_SEPARATOR . '*') ?: [] as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
        rmdir($this->directory);
    }

    public function testIdempotentEnqueueAndIdentityCollision(): void
    {
        $first = $this->queue->enqueue('lab', 'scientific-run-900001', 'lab-900001-key', 'stems', 'gpu', 50);
        $again = $this->queue->enqueue('lab', 'scientific-run-900001', 'lab-900001-key', 'stems', 'gpu', 50);
        self::assertSame($first['id'], $again['id']);
        $this->expectException(\DomainException::class);
        $this->queue->enqueue('lab', 'scientific-run-900001', 'lab-900001-key', 'expertise.profile', 'gpu', 50);
    }

    public function testPriorityAndSingleAtomicClaim(): void
    {
        $low = $this->queue->enqueue('lab', 'low', 'low-key', 'stems', 'gpu', 10);
        $high = $this->queue->enqueue('lab', 'high', 'high-key', 'expertise.profile', 'gpu', 90);
        $cpu = $this->queue->enqueue('dev', 'cpu', 'cpu-key', 'chords', 'cpu', 99);
        $first = $this->queue->claim('gpu');
        self::assertNotNull($first);
        self::assertSame((int) $high['id'], (int) $first['id']);
        self::assertSame('running', $first['state']);
        self::assertSame(1, (int) $first['claim_generation']);
        $second = $this->queue->claim('gpu');
        self::assertSame((int) $low['id'], (int) $second['id']);
        self::assertNull($this->queue->claim('gpu'));
        self::assertSame((int) $cpu['id'], (int) $this->queue->claim('cpu')['id']);
    }

    public function testForeignLeaseCannotFinishOrHeartbeat(): void
    {
        $this->queue->enqueue('lab', 'job', 'job-key', 'stems', 'gpu');
        $running = $this->queue->claim('gpu');
        self::assertNotNull($running);
        $invalid = str_repeat('0', 64);
        self::assertNotSame($invalid, $running['lease_token']);
        try {
            $this->queue->finish((int) $running['id'], $invalid, true);
            self::fail('Expected lease rejection');
        } catch (\DomainException $e) {
            self::assertSame('lease_not_current', $e->getMessage());
        }
        $this->expectException(\DomainException::class);
        $this->queue->heartbeat((int) $running['id'], $invalid);
    }

    public function testHeartbeatAndProducerScopedEvents(): void
    {
        $this->queue->enqueue('lab', 'job', 'job-key', 'stems', 'gpu');
        $job = $this->queue->claim('gpu');
        self::assertNotNull($job);
        $event = $this->queue->heartbeat((int) $job['id'], (string) $job['lease_token'], 120, 20, 'analyse', 'progression');
        self::assertSame(20, $event['progress_percent']);
        self::assertCount(1, $this->queue->events('lab'));
        self::assertSame([], $this->queue->events('dev'));
        try {
            $this->queue->heartbeat((int) $job['id'], (string) $job['lease_token'], 120, 19);
            self::fail('Expected monotonic progress rejection');
        } catch (\DomainException $e) {
            self::assertSame('progress_regression', $e->getMessage());
        }
        self::assertSame('completed', $this->queue->finish((int) $job['id'], (string) $job['lease_token'], true)['state']);
        $this->expectException(\DomainException::class);
        $this->queue->finish((int) $job['id'], (string) $job['lease_token'], true);
    }
}
