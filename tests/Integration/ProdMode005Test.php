<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\ProdModeCommand;
use Symfony\Component\Console\Tester\CommandTester;

final class ProdMode005Test extends TestCase
{
    public function testInvalidActionCannotMutateProd(): void
    {
        $tester = new CommandTester(new ProdModeCommand(new \Ezs\Web\Module\Infrastructure\ProdModeService()));
        $code = $tester->execute(['action' => 'invalid-test-action']);
        self::assertNotSame(0, $code);
    }

    public function testRetiredProdEntrypointIsAbsent(): void
    {
        self::assertFileDoesNotExist(dirname(__DIR__, 2) . '/bin/prod_mode.php');
    }
}
