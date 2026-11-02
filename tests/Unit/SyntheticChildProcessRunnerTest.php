<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExecutorOwnershipRegistry;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\SyntheticChildProcessRunner;
use PHPUnit\Framework\TestCase;

final class SyntheticChildProcessRunnerTest extends TestCase
{
    private string $dir;
    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite unavailable');
        if (!function_exists('proc_open')) self::markTestSkipped('proc_open unavailable');
        $this->dir = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_child_'.bin2hex(random_bytes(8));
        if (!mkdir($this->dir, 0700)) throw new \RuntimeException('test_directory_unavailable');
    }
    protected function tearDown(): void
    {
        if (!isset($this->dir)) return;
        foreach (glob($this->dir.'/*') ?: [] as $file) unlink($file);
        rmdir($this->dir);
    }
    private function fixture(): string
    {
        $file = $this->dir.'/fixture.php';
        file_put_contents($file, '<?php usleep(300000); echo "EZS_SYNTHETIC_CHILD_OK\\n";');
        return $file;
    }
    public function testRealChildIsRegisteredAndCompletedInIsolatedQueue(): void
    {
        $path = $this->dir.'/queue.sqlite';
        $queue = new GlobalQueueStore($path);
        $queue->enqueue('EZS_SYNTHETIC', 'c1', 'key-c1', 'synthetic_child', 'cpu');
        $ownership = new ExecutorOwnershipRegistry($path);
        $runner = new SyntheticChildProcessRunner($queue, $ownership, $path);
        $result = $runner->runOne(PHP_BINARY, $this->fixture(), static fn(int $pid): array => [
            'pid'=>$pid, 'node'=>'TEST', 'created_at'=>'synthetic-test-observation', 'instance_id'=>'test-run-1',
        ]);
        self::assertSame('completed', $result['state']);
        self::assertGreaterThan(0, $result['pid']);
        self::assertSame($result['pid'], (int) $ownership->forClaim($result['job_id'], 1)['pid']);
        self::assertSame('completed', $queue->byId($result['job_id'])['state']);
    }
    public function testMismatchNeverMarksChildSuccessful(): void
    {
        $path = $this->dir.'/queue.sqlite';
        $queue = new GlobalQueueStore($path);
        $job = $queue->enqueue('EZS_SYNTHETIC', 'c2', 'key-c2', 'synthetic_child', 'cpu');
        $ownership = new ExecutorOwnershipRegistry($path);
        $runner = new SyntheticChildProcessRunner($queue, $ownership, $path);
        try {
            $runner->runOne(PHP_BINARY, $this->fixture(), static fn(int $pid): array => [
                'pid'=>$pid+1, 'node'=>'TEST', 'created_at'=>'wrong', 'instance_id'=>'wrong',
            ]);
            self::fail('forged observation accepted');
        } catch (\DomainException $e) {
            self::assertSame('synthetic_child_observation_mismatch', $e->getMessage());
        }
        self::assertSame('running', $queue->byId((int)$job['id'])['state']);
        self::assertNull($ownership->forClaim((int)$job['id'], 1));
    }
}
