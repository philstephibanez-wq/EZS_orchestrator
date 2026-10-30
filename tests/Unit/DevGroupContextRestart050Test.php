<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\Controller\DevGroupOperationsController;

final class DevGroupContextRestart050Test extends TestCase
{
    public function testContextualPermissionsAndIsolatedRestartContract(): void
    {
        $states = array_fill_keys(array_keys(\Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle::specs()), 'ATTESTED');
        $up = DevGroupOperationsController::permission($states, 'lab');
        self::assertSame(['start'=>false,'restart'=>true,'stop'=>true,'state'=>'RUNNING'], $up);
        $states['lab'] = 'ABSENT';
        self::assertSame(['start'=>true,'restart'=>false,'stop'=>false,'state'=>'STOPPED'], DevGroupOperationsController::permission($states, 'lab'));
        $states['lab'] = 'PORT_UNVERIFIED';
        self::assertSame('UNVERIFIED', DevGroupOperationsController::permission($states, 'lab')['state']);
        self::assertFalse(DevGroupOperationsController::permission($states, 'lab')['restart']);
        $controller = file_get_contents(__DIR__.'/../../src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("'action' => 'start|stop|restart'", $controller);
        self::assertStringContainsString("$".'lifecycle->stopGroup($group)', $controller);
        self::assertStringContainsString("$".'lifecycle->startGroup($group)', $controller);
        self::assertStringContainsString("'restart_incomplete'", $controller);
    }
}
