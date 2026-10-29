<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\EcosystemEntryCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Output\BufferedOutput;

final class EcosystemEntry011Test extends TestCase
{
    public function testUnknownActionIsRefusedWithoutLaunching(): void
    {
        $out = new BufferedOutput();
        self::assertSame(Command::INVALID, EcosystemEntryCommand::invoke('restart-prod', false, $out));
        self::assertStringContainsString('ACTION_REFUSED', $out->fetch());
    }
    public function testStartPlanNeverStartsProcesses(): void
    {
        $out = new BufferedOutput();
        self::assertSame(Command::SUCCESS, EcosystemEntryCommand::invoke('start', true, $out));
        self::assertStringContainsString('ENGINE=LEGACY_POWERSHELL_TRANSITION', $out->fetch());
    }
    public function testStopPlanNeverStopsProd(): void
    {
        $out = new BufferedOutput();
        self::assertSame(Command::SUCCESS, EcosystemEntryCommand::invoke('stop', true, $out));
        self::assertStringContainsString('PLAN=STOP', $out->fetch());
    }
}
