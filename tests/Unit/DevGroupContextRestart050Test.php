<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\Controller\DevGroupOperationsController;

final class DevGroupContextRestart050Test extends TestCase
{
    public function testContextualPermissionsAndIsolatedNativeRestartContract(): void
    {
        $states=['ezscore_dev'=>'ATTESTED','ezscore_preview'=>'ATTESTED',
            'lab'=>'ATTESTED','assistant'=>'ATTESTED'];
        self::assertSame(['start'=>false,'restart'=>true,'stop'=>true,'state'=>'RUNNING'],
            DevGroupOperationsController::permission($states,'lab'));
        $states['lab']='ABSENT';
        self::assertSame('STOPPED', DevGroupOperationsController::permission($states,'lab')['state']);
        $states['lab']='PORT_UNVERIFIED';
        self::assertSame('UNVERIFIED', DevGroupOperationsController::permission($states,'lab')['state']);
        self::assertFalse(DevGroupOperationsController::permission($states,'lab')['restart']);
        $controller=(string)file_get_contents(__DIR__.'/../../src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("'action'=>'start|stop|restart'",$controller);
        self::assertStringContainsString('$native->stop($group)',$controller);
        self::assertStringContainsString('$native->start($group)',$controller);
        self::assertStringContainsString("'restart_incomplete'",$controller);
        self::assertStringNotContainsString('NativeWindowsLifecycle',$controller);
    }
}
