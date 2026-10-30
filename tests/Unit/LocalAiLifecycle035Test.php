<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\LocalAiLifecycle;
use PHPUnit\Framework\TestCase;

final class LocalAiLifecycle035Test extends TestCase
{
    private static function process(int $pid=17,string $command=''):array
    {
        $args=array_map(static fn(string $v):string=>'"'.$v.'"', [LocalAiLifecycle::EXE,...LocalAiLifecycle::arguments()]);
        return ['pid'=>$pid,'executable'=>LocalAiLifecycle::EXE,'command'=>$command!==''?$command:implode(' ',$args),'created'=>'20261030010500.000000+060'];
    }
    private static function service(callable $inventory,callable $listeners,callable $health,callable $spawn):LocalAiLifecycle
    {
        // All external observations are mocked: never probe the real Windows TCP table.
        return new LocalAiLifecycle($inventory,$listeners,$health,$spawn,static fn(string $p):bool=>true,
            static fn(int $port):?int=>null);
    }
    public function testExistingServerIsAdoptedWithoutSpawning():void
    {
        $spawns=0;
        $svc=self::service(static fn():array=>[self::process()],static fn():array=>[8720=>[17]],static fn():bool=>true,
            static function()use(&$spawns):int{$spawns++;return 44;});
        self::assertSame(['pid'=>17,'action'=>'ALREADY_READY'],$svc->start());
        self::assertSame(0,$spawns);
    }
    public function testAbsentServerIsStartedAndVerified():void
    {
        $count=0;$spawns=0;
        $svc=self::service(static function()use(&$count):array{return $count++===0?[]:[self::process(45)];},
            static function()use(&$count):array{return $count<2?[]:[8720=>[45]];},static fn():bool=>true,
            static function()use(&$spawns):int{$spawns++;return 45;});
        self::assertSame(['pid'=>45,'action'=>'STARTED'],$svc->start());
        self::assertSame(1,$spawns);
    }
    public function testForeignPortOwnerIsRefusedWithoutSpawn():void
    {
        $svc=self::service(static fn():array=>[['pid'=>99,'executable'=>'C:/other/llama-server.exe','command'=>'other']],
            static fn():array=>[8720=>[99]],static fn():bool=>true,static fn():int=>throw new \LogicException('unexpected spawn'));
        $this->expectExceptionMessage('EZS_AI_PORT_FOREIGN');$svc->start();
    }
    public function testUnknownOrUnlisteningLlamaIsNotDuplicated():void
    {
        $svc=self::service(static fn():array=>[self::process()],static fn():array=>[],static fn():bool=>false,
            static fn():int=>throw new \LogicException('unexpected spawn'));
        $this->expectExceptionMessage('EZS_AI_PROCESS_WITHOUT_LISTENER');$svc->start();
    }
    public function testUnhealthyOwnedServerIsRefused():void
    {
        $svc=self::service(static fn():array=>[self::process()],static fn():array=>[8720=>[17]],static fn():bool=>false,
            static fn():int=>throw new \LogicException('unexpected spawn'));
        $this->expectExceptionMessage('EZS_AI_OWNED_NOT_READY');$svc->start();
    }
    public function testMissingDependencyIsRefused():void
    {
        $svc=new LocalAiLifecycle(static fn():array=>[],static fn():array=>[],static fn():bool=>false,
            static fn():int=>throw new \LogicException('unexpected spawn'),static fn(string $path):bool=>false);
        $this->expectExceptionMessage('EZS_AI_DEPENDENCY_MISSING');$svc->start();
    }
    public function testAlteredCommandIsRejected():void
    {
        $svc=self::service(static fn():array=>[self::process(17,'"'.LocalAiLifecycle::EXE.'" -m evil.gguf --port 8720')],
            static fn():array=>[8720=>[17]],static fn():bool=>true,
            static fn():int=>throw new \LogicException('unexpected spawn'));
        $this->expectExceptionMessage('EZS_AI_PORT_FOREIGN');$svc->start();
    }
}
