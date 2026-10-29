<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\EcosystemEntryCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Output\BufferedOutput;
final class EcosystemEntry011Test extends TestCase
{
    public function testUnknownActionRefusedWithoutLaunching():void
    {
        $out=new BufferedOutput();
        self::assertSame(Command::INVALID,EcosystemEntryCommand::invoke('restart-prod',false,$out));
        self::assertStringContainsString('ACTION_REFUSED',$out->fetch());
    }
    public function testNativeStartPlanDoesNotMutate():void
    {
        $out=new BufferedOutput();
        self::assertSame(Command::SUCCESS,EcosystemEntryCommand::invoke('start',true,$out));
        self::assertStringContainsString('ENGINE=NATIVE_WINDOWS_WMI',$out->fetch());
    }
    public function testNativeStopPlanDoesNotMutateProd():void
    {
        $out=new BufferedOutput();
        self::assertSame(Command::SUCCESS,EcosystemEntryCommand::invoke('stop',true,$out));
        self::assertStringContainsString('PLAN=STOP',$out->fetch());
    }
}
