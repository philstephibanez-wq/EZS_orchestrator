<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use Ezs\Web\Module\Coordination\{ExecutorOwnershipRegistry,ExpiredLeaseSweep,GlobalQueueStore,TrustedLeaseRecovery};
use PHPUnit\Framework\TestCase;
final class TrustedLeaseRecoveryTest extends TestCase
{
    private string $database;
    protected function setUp(): void { $this->database=sys_get_temp_dir().'/trusted_recovery_'.bin2hex(random_bytes(10)).'.sqlite'; }
    protected function tearDown(): void { foreach (['','-wal','-shm'] as $suffix) @unlink($this->database.$suffix); }
    public function testMissingOwnershipMustNotInvokeProbe(): void
    {
        $store=new GlobalQueueStore($this->database);
        $store->enqueue('LAB','one','one','analysis','gpu');
        $job=$store->claim('gpu');
        $calls=0;
        $recovery=new TrustedLeaseRecovery(new ExpiredLeaseSweep($store),new ExecutorOwnershipRegistry($this->database),static function(array $p) use (&$calls):array {++$calls;return ['status'=>'stopped_confirmed'];});
        $outcome=$recovery->run();
        self::assertSame(1,$outcome['blocked']);self::assertSame(0,$outcome['recovered']);self::assertSame(0,$calls);
        self::assertSame('running',$store->byId((int)$job['id'])['state']);
    }
    public function testOwnershipRequiresExactIndependentAttestation(): void
    {
        $store=new GlobalQueueStore($this->database);
        $store->enqueue('LAB','two','two','analysis','gpu');
        $job=$store->claim('gpu');$id=(int)$job['id'];
        $registry=new ExecutorOwnershipRegistry($this->database);
        $registry->register($id,(int)$job['claim_generation'],$job['lease_token'],'MAIN',1234,'2026-11-02T07:00:00Z','launch-1');
        $probe=static fn(array $owner):array=>['status'=>'stopped_confirmed','node'=>$owner['node'],'pid'=>$owner['pid'],'created_at'=>$owner['created_at'],'instance_id'=>$owner['instance_id']];
        $wrong=new TrustedLeaseRecovery(new ExpiredLeaseSweep($store),$registry,static function(array $owner) use($probe):array {$v=$probe($owner);$v['instance_id']='different';return $v;});
        self::assertSame(1,$wrong->run()['blocked']);
        self::assertSame('running',$store->byId($id)['state']);
        $trusted=new TrustedLeaseRecovery(new ExpiredLeaseSweep($store),$registry,$probe);
        self::assertSame(1,$trusted->run()['recovered']);
        self::assertSame('queued',$store->byId($id)['state']);
        $this->expectException(\DomainException::class);
        $store->finish($id,$job['lease_token'],true);
    }
}
