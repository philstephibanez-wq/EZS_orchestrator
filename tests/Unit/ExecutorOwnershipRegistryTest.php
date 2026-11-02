<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExecutorOwnershipRegistry;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

final class ExecutorOwnershipRegistryTest extends TestCase
{
    private string $dir;
    protected function setUp(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite unavailable');
        $this->dir = sys_get_temp_dir().DIRECTORY_SEPARATOR.'ownership_'.bin2hex(random_bytes(10));
        if (!mkdir($this->dir, 0700)) throw new \RuntimeException('test_directory_unavailable');
    }
    protected function tearDown(): void
    {
        if (!isset($this->dir)) return;
        foreach (glob($this->dir.DIRECTORY_SEPARATOR.'*') ?: [] as $file) unlink($file);
        rmdir($this->dir);
    }
    public function testCurrentClaimRegistrationIsDurableImmutableAndIdempotent(): void
    {
        $path = $this->dir.'/queue.sqlite';
        $queue = new GlobalQueueStore($path);
        $queue->enqueue('LAB','unit-1','key-1','profile','gpu');
        $job = $queue->claim('gpu');
        $registry = new ExecutorOwnershipRegistry($path);
        $args = [(int)$job['id'],(int)$job['claim_generation'],$job['lease_token'],'MAIN',1234,'2026-11-02T01:00:00Z','run-1'];
        $registered = $registry->register(...$args);
        self::assertSame('MAIN',$registered['node']);
        self::assertSame($registered,$registry->register(...$args));
        self::assertSame('run-1',(new ExecutorOwnershipRegistry($path))->forClaim($args[0],$args[1])['instance_id']);
        $this->expectExceptionMessage('executor_identity_collision');
        $registry->register($args[0],$args[1],$args[2],'MAIN',9999,$args[5],$args[6]);
    }
    public function testStaleOrForgedLeaseCannotRegister(): void
    {
        $path = $this->dir.'/queue.sqlite';
        $queue = new GlobalQueueStore($path);
        $queue->enqueue('LAB','unit-2','key-2','profile','cpu');
        $job = $queue->claim('cpu');
        $registry = new ExecutorOwnershipRegistry($path);
        try {
            $registry->register((int)$job['id'],(int)$job['claim_generation'],str_repeat('0',64),'MAIN',1,'start','run');
            self::fail('forged token accepted');
        } catch (\DomainException $e) {
            self::assertSame('executor_claim_not_current',$e->getMessage());
        }
        $queue->finish((int)$job['id'],$job['lease_token'],true);
        $this->expectExceptionMessage('executor_claim_not_current');
        $registry->register((int)$job['id'],(int)$job['claim_generation'],$job['lease_token'],'MAIN',1,'start','run');
    }
}
