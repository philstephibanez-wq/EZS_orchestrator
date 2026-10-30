<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\EcosystemEntryCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Output\BufferedOutput;
final class EcosystemAiStart037Test extends TestCase
{
    public function testAiStartsAfterDevAndReusesAnExistingServer():void
    {
        $calls=[];$out=new BufferedOutput();
        $code=EcosystemEntryCommand::invoke('start',false,$out,
            static function()use(&$calls):array{$calls[]='dev';return ['root_php'=>17];},
            static function()use(&$calls):array{$calls[]='ai';return ['pid'=>18,'action'=>'ALREADY_READY'];});
        self::assertSame(Command::SUCCESS,$code);
        self::assertSame(['dev','ai'],$calls);
        $text=$out->fetch();
        self::assertStringContainsString('EZS_AI_START_OWNED_READY_8720 PID=18 ACTION=ALREADY_READY',$text);
    }
    public function testAiFailureIsAnExplicitPartialStartAndDevIsNotRolledBack():void
    {
        $calls=[];$out=new BufferedOutput();
        $code=EcosystemEntryCommand::invoke('start',false,$out,
            static function()use(&$calls):array{$calls[]='dev';return ['root_php'=>17];},
            static function()use(&$calls):array{$calls[]='ai';throw new RuntimeException('EZS_AI_PORT_FOREIGN');});
        self::assertSame(Command::FAILURE,$code);
        self::assertSame(['dev','ai'],$calls);
        self::assertStringContainsString('EZS_ECOSYSTEM_PARTIAL_DEV_READY_AI_REFUSED:EZS_AI_PORT_FOREIGN',$out->fetch());
    }
    public function testDevFailurePreventsAiStart():void
    {
        $calls=[];$out=new BufferedOutput();
        $code=EcosystemEntryCommand::invoke('start',false,$out,
            static function()use(&$calls):array{$calls[]='dev';throw new RuntimeException('EZS_NATIVE_BUSY');},
            static function()use(&$calls):array{$calls[]='ai';return ['pid'=>18,'action'=>'STARTED'];});
        self::assertSame(Command::FAILURE,$code);
        self::assertSame(['dev'],$calls);
        self::assertStringContainsString('EZS_NATIVE_START_REFUSED:EZS_NATIVE_BUSY',$out->fetch());
    }
    public function testPlanNeverCallsAnyStart():void
    {
        $out=new BufferedOutput();
        $code=EcosystemEntryCommand::invoke('start',true,$out,
            static fn():array=>throw new LogicException('dev started'),
            static fn():array=>throw new LogicException('ai started'));
        self::assertSame(Command::SUCCESS,$code);
        self::assertStringContainsString('EZS_ECOSYSTEM_AI_START=LOCAL_AI_LIFECYCLE_8720',$out->fetch());
    }
    public function testInvalidAiResultDoesNotPretendToBeReady():void
    {
        $out=new BufferedOutput();
        $code=EcosystemEntryCommand::invoke('start',false,$out,
            static fn():array=>[],static fn():array=>['pid'=>0,'action'=>'STARTED']);
        self::assertSame(Command::FAILURE,$code);
        self::assertStringContainsString('EZS_AI_RESULT_INVALID',$out->fetch());
    }
}
