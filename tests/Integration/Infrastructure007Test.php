<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\InfrastructureCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Tester\CommandTester;

final class Infrastructure007Test extends TestCase
{
    public function testUnknownDiagnosticIsRejected(): void
    {
        $tester = new CommandTester(new InfrastructureCommand());
        self::assertSame(Command::INVALID, $tester->execute(['action' => 'unsupported']));
    }

    public function testRetiredEntrypointIsAbsent(): void
    {
        self::assertFileDoesNotExist(dirname(__DIR__, 2) . '/bin/infrastructure.php');
    }
}
