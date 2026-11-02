<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\SyntheticCpuQueueRunner;
use PHPUnit\Framework\TestCase;

final class SyntheticCpuQueueRunnerTest extends TestCase
{
    private string $dir;

    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite unavailable');
        $this->dir = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_cpu_run_'.bin2hex(random_bytes(10));
        if (!mkdir($this->dir, 0700)) throw new \RuntimeException('test_directory_unavailable');
    }

    protected function tearDown(): void
    {
        if (!isset($this->dir)) return;
        foreach (glob($this->dir.DIRECTORY_SEPARATOR.'*') ?: [] as $file) unlink($file);
        rmdir($this->dir);
    }

    private function store(): GlobalQueueStore
    {
        return new GlobalQueueStore($this->dir.DIRECTORY_SEPARATOR.'synthetic.sqlite');
    }

    public function testOneShotCpuRunsHeartbeatAndFinishesInCanonicalQueue(): void
    {
        $store = $this->store();
        $cpu = $store->enqueue('LAB', 'cpu-fixture', 'cpu-fixture-key', 'synthetic', 'cpu');
        $gpu = $store->enqueue('LAB', 'gpu-fixture', 'gpu-fixture-key', 'synthetic', 'gpu');
        $invoked = 0;
        $runner = new SyntheticCpuQueueRunner($store);
        $result = $runner->runOne(function (array $envelope, \Closure $progress) use (&$invoked, $cpu): void {
            ++$invoked;
            self::assertSame((int) $cpu['id'], $envelope['id']);
            self::assertArrayNotHasKey('lease_token', $envelope);
            $progress(40);
        });
        self::assertSame(1, $invoked);
        self::assertSame(['claimed' => true, 'job_id' => (int) $cpu['id'], 'state' => 'completed'], $result);
        self::assertSame('completed', $store->byId((int) $cpu['id'])['state']);
        self::assertSame('queued', $store->byId((int) $gpu['id'])['state']);
        self::assertCount(1, $store->events('LAB'));
        self::assertSame(['claimed' => false], $runner->runOne(static function (): void { self::fail('Unexpected execution'); }));
    }

    public function testCallbackFailureMarksCpuFailedWithoutConsumingGpu(): void
    {
        $store = $this->store();
        $cpu = $store->enqueue('Assistant', 'cpu-error', 'cpu-error-key', 'synthetic', 'cpu');
        $gpu = $store->enqueue('Assistant', 'gpu-pending', 'gpu-pending-key', 'synthetic', 'gpu');
        try {
            (new SyntheticCpuQueueRunner($store))->runOne(static function (): void {
                throw new \RuntimeException('synthetic_failure');
            });
            self::fail('Exception should reach the caller');
        } catch (\RuntimeException $e) {
            self::assertSame('synthetic_failure', $e->getMessage());
        }
        self::assertSame('failed', $store->byId((int) $cpu['id'])['state']);
        self::assertSame('queued', $store->byId((int) $gpu['id'])['state']);
    }
}
