<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\GatewayMonitorCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Tester\CommandTester;

final class GatewayMonitor006Test extends TestCase
{
    public function testInvalidActionIsRefusedBeforeAnyMonitoring(): void
    {
        $command = new GatewayMonitorCommand();
        $tester = new CommandTester($command);
        $code = $tester->execute(['action' => 'unsupported']);
        self::assertSame(Command::INVALID, $code);
    }

    public function testRetiredEntrypointIsAbsent(): void
    {
        self::assertFileDoesNotExist(dirname(__DIR__, 2) . '/bin/gateway_monitor.php');
    }
}
