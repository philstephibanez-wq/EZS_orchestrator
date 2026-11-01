<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\Messenger\QueueJobReference;
use Ezs\Web\Module\Coordination\Messenger\QueueJobReferenceAdapter;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

final class QueueJobReferenceAdapterTest extends TestCase
{
    private string $path;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite absent');
        }
        $directory = sys_get_temp_dir() . '/ezs-d9-' . bin2hex(random_bytes(10));
        if (!mkdir($directory, 0700) && !is_dir($directory)) {
            throw new \RuntimeException('synthetic_queue_directory_unavailable');
        }
        $this->path = $directory . '/synthetic.sqlite';
    }

    protected function tearDown(): void
    {
        if (!isset($this->path)) {
            return;
        }
        foreach ([$this->path, $this->path . '-wal', $this->path . '-shm'] as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
        rmdir(dirname($this->path));
    }

    public function testReadOnlyReferenceAndProducerIsolation(): void
    {
        $store = new GlobalQueueStore($this->path);
        $job = $store->enqueue('lab', 'synthetic-1', 'synthetic-key-1', 'profile', 'cpu', 40);
        $adapter = new QueueJobReferenceAdapter();
        $reference = new QueueJobReference((int) $job['id'], 'lab');
        $result = $adapter->inspect($reference, $this->path);
        self::assertSame('queued', $result['state']);
        self::assertSame('lab', $result['producer']);
        self::assertArrayNotHasKey('lease_token', $result);
        self::assertArrayNotHasKey('idempotency_key', $result);
        self::assertSame('queued', $store->byId((int) $job['id'])['state']);
        try {
            $adapter->inspect(new QueueJobReference((int) $job['id'], 'assistant'), $this->path);
            self::fail('Producer isolation missing');
        } catch (\DomainException $e) {
            self::assertSame('queue_job_not_found', $e->getMessage());
        }
    }

    public function testGenerationMismatchCannotBeAccepted(): void
    {
        $store = new GlobalQueueStore($this->path);
        $job = $store->enqueue('assistant', 'synthetic-2', 'synthetic-key-2', 'review', 'cpu');
        $claimed = $store->claim('cpu');
        self::assertSame((int) $job['id'], (int) $claimed['id']);
        self::assertSame(1, (int) $claimed['claim_generation']);
        $adapter = new QueueJobReferenceAdapter();
        try {
            $adapter->inspect(new QueueJobReference((int) $job['id'], 'assistant', 0), $this->path);
            self::fail('Stale generation accepted');
        } catch (\DomainException $e) {
            self::assertSame('queue_job_generation_mismatch', $e->getMessage());
        }
        self::assertSame('running', $adapter->inspect(new QueueJobReference((int) $job['id'], 'assistant', 1), $this->path)['state']);
    }

    public function testInvalidReferenceRejected(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        new QueueJobReference(0, 'prod');
    }
}
