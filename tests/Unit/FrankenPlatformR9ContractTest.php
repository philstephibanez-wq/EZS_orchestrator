<?php

declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\DevWebModeController;
use PHPUnit\Framework\TestCase;

final class FrankenPlatformR9ContractTest extends TestCase
{
    public function testPilotContainsFourSitesAndNoProdListener(): void
    {
        $root=dirname(__DIR__,2);
        $conf=(string) file_get_contents($root.'/config/frankenphp/Caddyfile.platform.r9');
        foreach (['8790','8502','8602','8701','8702','8712','8713'] as $p) {
            self::assertStringContainsString('127.0.0.1:'.$p,$conf);
        }
        foreach (['http://127.0.0.1:8501','http://127.0.0.1:8510',
            'http://127.0.0.1:8511','php_fastcgi','php-cgi'] as $unsafe) {
            self::assertStringNotContainsString($unsafe,$conf);
        }
        self::assertStringContainsString('env APP_ENV dev',$conf);
        self::assertStringContainsString('forward_auth 127.0.0.1:8602',$conf);
        self::assertStringContainsString('header Retry-After "120"',$conf);
        self::assertStringContainsString('dev.maintenance',$conf);
    }

    public function testOnlyServiceHostsAndResidentNeverStartsSites(): void
    {
        $root=dirname(__DIR__,2);
        $xml=(string) file_get_contents($root.'/config/frankenphp/EZS_FrankenPHP.pilot.xml');
        self::assertStringContainsString('Caddyfile.platform.r9',$xml);
        self::assertStringContainsString('<startmode>Automatic</startmode>',$xml);
        $resident=(string) file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringNotContainsString('-Action Boot',$resident);
        self::assertStringNotContainsString('ezs_boot_sites_r7.ps1',$resident);
        self::assertStringNotContainsString('Start-Process',$resident);
    }

    public function testDevModeRestrictedAndNoProcessMutation(): void
    {
        self::assertTrue(DevWebModeController::allowed('dev','localhost','127.0.0.1'));
        self::assertFalse(DevWebModeController::allowed('prod','localhost','127.0.0.1'));
        self::assertFalse(DevWebModeController::allowed('dev','example.com','127.0.0.1'));
        $src=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/Controller/DevWebModeController.php');
        self::assertStringNotContainsString('Stop-Process',$src);
        self::assertStringNotContainsString('Start-Process',$src);
        self::assertStringContainsString('dev_mode_not_confirmed',$src);
    }
}
