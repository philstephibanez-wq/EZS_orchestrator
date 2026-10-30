<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\LocalAiLifecycle;
use PHPUnit\Framework\TestCase;

final class LocalAiActiveProof038Test extends TestCase
{
    private static function process(int $pid=1676,?string $command=null):array
    {
        $parts=[LocalAiLifecycle::EXE,...LocalAiLifecycle::arguments()];
        $quoted=implode(' ',array_map(static fn(string $part):string=>'"'.$part.'"',$parts));
        return ['pid'=>$pid,'executable'=>LocalAiLifecycle::EXE,'command'=>$command??$quoted];
    }
    private static function service(array $inventory,array $listeners,callable $proof,?callable $spawn=null,?callable $health=null):LocalAiLifecycle
    {
        return new LocalAiLifecycle(static fn():array=>$inventory,static fn():array=>$listeners,$health??static fn():bool=>true,
            $spawn??static fn():int=>throw new LogicException('unexpected spawn'),static fn(string $p):bool=>true,$proof);
    }
    public function testPidZeroIsResolvedByActiveProofWithoutSpawning():void
    {
        $calls=0;
        $svc=self::service([self::process()],[8720=>[0]],static function(int $port)use(&$calls):int{
            self::assertSame(8720,$port);$calls++;return 1676;
        });
        self::assertSame(['pid'=>1676,'action'=>'ALREADY_READY'],$svc->start());
        self::assertSame(1,$calls);
    }
    public function testMissingListenerCanBeResolvedByActiveProof():void
    {
        $svc=self::service([self::process()],[],static fn(int $port):int=>1676);
        self::assertSame(['pid'=>1676,'action'=>'ALREADY_READY'],$svc->start());
    }
    public function testVisibleForeignPidIsNeverOverriddenByProof():void
    {
        $svc=self::service([self::process()],[8720=>[999]],static fn(int $port):int=>1676);
        $this->expectExceptionMessage('EZS_AI_PORT_FOREIGN');
        $svc->start();
    }
    public function testUnattributedPortWithoutProofIsRefusedWithoutSpawn():void
    {
        $svc=self::service([self::process()],[8720=>[0]],static fn(int $port):?int=>null);
        $this->expectExceptionMessage('EZS_AI_PORT_UNVERIFIED');
        $svc->start();
    }
    public function testActiveProofForeignPidIsRejected():void
    {
        $svc=self::service([self::process()],[8720=>[0]],static fn(int $port):int=>999);
        $this->expectExceptionMessage('EZS_AI_PORT_FOREIGN');
        $svc->start();
    }
    public function testActiveProofRequiresFullCommandIdentity():void
    {
        $svc=self::service([self::process(1676,'"'.LocalAiLifecycle::EXE.'" -m other.gguf')],[8720=>[0]],static fn(int $port):int=>1676);
        $this->expectExceptionMessage('EZS_AI_PORT_FOREIGN');
        $svc->start();
    }
    public function testProofOwnerWithUnhealthyServerIsRefused():void
    {
        $svc=self::service([self::process()],[8720=>[0]],static fn(int $port):int=>1676,null,static fn():bool=>false);
        $this->expectExceptionMessage('EZS_AI_OWNED_NOT_READY');
        $svc->start();
    }
    public function testMultipleListenerOwnersAreRefused():void
    {
        $svc=self::service([self::process()],[8720=>[0,1676]],static fn(int $port):int=>1676);
        $this->expectExceptionMessage('EZS_AI_PORT_MULTIPLE_OWNERS');
        $svc->start();
    }
}
