<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Tester\CommandTester;
use Ezs\Web\Module\Infrastructure\EcosystemStatusCommand;
use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;

final class EcosystemStatusCommand014Test extends TestCase
{
    public function testStatusIsReadOnlyWithDeterministicWindowsInventory(): void
    {
        $inventory = new WindowsProcessInventory(static fn(): iterable => []);
        $command = new EcosystemStatusCommand($inventory);
        $tester = new CommandTester($command);
        self::assertSame(0, $tester->execute([]));
        self::assertStringContainsString('EZS_STATUS=READ_ONLY_WMI_OBSERVATION', $tester->getDisplay());
        self::assertStringContainsString('EZS_PROD_ATTESTATION=NOT_IMPLEMENTED', $tester->getDisplay());
    }
}
