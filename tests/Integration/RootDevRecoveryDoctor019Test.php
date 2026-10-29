<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\RootDevRecoveryDoctorCommand;
use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;
use Symfony\Component\Console\Application;
final class RootDevRecoveryDoctor019Test extends TestCase
{
    public function testDoctorCommandRegisteredWithoutExecutingNativeTools(): void {
        $app=new Application();$app->add(new RootDevRecoveryDoctorCommand(new WindowsProcessInventory(static fn():iterable=>[])));
        self::assertInstanceOf(RootDevRecoveryDoctorCommand::class,$app->find('ezs:dev:doctor'));
    }
}
