<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use Ezs\Web\Module\Coordination\{ExpiredLeaseSweep,GlobalQueueStore};
use PHPUnit\Framework\TestCase;
final class ExpiredLeaseSweepTest extends TestCase
{
    private string $database;
    protected function setUp(): void { $this->database = sys_get_temp_dir().'/ezs_stopped_sweep_'.bin2hex(random_bytes(10)).'.sqlite'; }
    protected function tearDown(): void { foreach (['','-wal','-shm'] as $suffix) @unlink($this->database.$suffix); }
    public function testUnattestedRunningJobStaysBlockedRegardlessOfTime(): void
    {
        $store=new GlobalQueueStore($this->database);
        $store->enqueue('LAB','one','sweep-one','analysis','gpu');
        $run=$store->claim('gpu');
        self::assertNull($run['lease_until']);
        $result=(new ExpiredLeaseSweep($store))->run(static fn(array $proof):bool => false);
        self::assertSame(['inspected'=>1,'recovered'=>0,'blocked'=>1,'stale'=>0,'errors'=>0],$result);
        self::assertSame('running',$store->byId((int)$run['id'])['state']);
    }
    public function testAttestedStoppedJobFencesOldToken(): void
    {
        $store=new GlobalQueueStore($this->database);
        $store->enqueue('LAB','one','sweep-one','analysis','gpu');
        $run=$store->claim('gpu');
        $proofs=[];
        $result=(new ExpiredLeaseSweep($store))->run(static function(array $proof) use (&$proofs):bool { $proofs[]=$proof;return true; });
        self::assertSame(1,$result['recovered']);
        self::assertSame((int)$run['claim_generation'],$proofs[0]['claim_generation']);
        self::assertArrayNotHasKey('lease_token',$proofs[0]);
        self::assertSame('queued',$store->byId((int)$run['id'])['state']);
        $this->expectException(\DomainException::class);
        $store->heartbeat((int)$run['id'],$run['lease_token']);
    }
    public function testLimitRejected(): void
    {
        $store=new GlobalQueueStore($this->database);
        $this->expectException(\InvalidArgumentException::class);
        (new ExpiredLeaseSweep($store))->run(static fn(array $proof):bool => false,101);
    }
}
