<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;
final class GlobalQueueRecoveryTest extends TestCase
{
    private string $database;
    protected function setUp(): void { $this->database=sys_get_temp_dir().'/ezs_recovery_'.bin2hex(random_bytes(10)).'.sqlite'; }
    protected function tearDown(): void { foreach (['','-wal','-shm'] as $suffix) @unlink($this->database.$suffix); }
    public function testStoppedJobRequiresProofAndOldTokenFenced(): void
    {
        $a=new GlobalQueueStore($this->database);
        $b=new GlobalQueueStore($this->database);
        $a->enqueue('LAB','song-1','one','analysis','gpu');
        $a->enqueue('LAB','song-2','two','analysis','gpu');
        $running=$a->claim('gpu');
        $id=(int)$running['id']; $gen=(int)$running['claim_generation'];$token=$running['lease_token'];
        self::assertNull($running['lease_until']);
        self::assertCount(1,$b->runningClaims());
        self::assertArrayNotHasKey('lease_token',$b->runningClaims()[0]);
        self::assertArrayNotHasKey('lease_until',$b->runningClaims()[0]);
        self::assertNull($b->claim('gpu'));
        try { $b->recoverStopped($id,$gen,static fn(array $p):bool => false); self::fail('Unattested recovery'); }
        catch(\DomainException $e) { self::assertSame('executor_not_attested_stopped',$e->getMessage()); }
        self::assertSame('running',$a->byId($id)['state']);
        $recovered=$b->recoverStopped($id,$gen,static fn(array $proof):bool => (int)$proof['id']===$id && $proof['claim_generation']===$gen);
        self::assertSame('queued',$recovered['state']);
        self::assertSame($gen+1,(int)$recovered['claim_generation']);
        foreach (['heartbeat','finish'] as $action) {
            try { if ($action==='heartbeat') $a->heartbeat($id,$token); else $a->finish($id,$token,true); self::fail('Old token accepted'); }
            catch(\DomainException $e) { self::assertSame('lease_not_current',$e->getMessage()); }
        }
        self::assertNotNull($a->claim('gpu'));
        self::assertCount(1,$b->events('LAB'));
    }
    public function testWrongGenerationRejectedAndHeartbeatDoesNotExpire(): void
    {
        $a=new GlobalQueueStore($this->database);
        $b=new GlobalQueueStore($this->database);
        $a->enqueue('LAB','song','key','analysis','gpu');
        $run=$a->claim('gpu');$id=(int)$run['id'];$gen=(int)$run['claim_generation'];
        $heartbeat=$a->heartbeat($id,$run['lease_token']);
        self::assertNull($heartbeat['lease_until']);
        try { $b->recoverStopped($id,$gen+1,static fn(array $p):bool => true); self::fail('Wrong generation accepted'); }
        catch(\DomainException $e) { self::assertSame('claim_not_running_current',$e->getMessage()); }
        self::assertSame('running',$b->byId($id)['state']);
        self::assertSame('completed',$a->finish($id,$run['lease_token'],true)['state']);
    }
}
