<?php

declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\DevWebModeController;
use PHPUnit\Framework\TestCase;

/** Final R9 contract: one shared FrankenPHP instance serves DEV and PROD. */
final class FrankenPlatformR9ContractTest extends TestCase
{
    public function testUnifiedPlatformContainsAllSitesAndProd(): void
    {
        $path = dirname(__DIR__, 2).'/config/frankenphp/Caddyfile.platform.unified';
        self::assertFileExists($path);
        $conf = (string) file_get_contents($path);
        foreach ([8790, 8502, 8602, 8701, 8702, 8712, 8713, 8501, 8510, 8511] as $port) {
            self::assertSame(1, preg_match('/^\\s*:' . $port . '\\s*\\{\\s*$/m', $conf));
        }
        self::assertStringContainsString('forward_auth 127.0.0.1:8602', $conf);
        self::assertStringContainsString('forward_auth 127.0.0.1:8510', $conf);
        self::assertStringContainsString('try_files dev.maintenance', $conf);
        self::assertStringContainsString('env APP_ENV prod', $conf);
        self::assertStringContainsString('env APP_DEBUG 0', $conf);
        self::assertStringNotContainsString('php_fastcgi', $conf);
        self::assertStringNotContainsString('php-cgi', $conf);
    }

    public function testResidentNeverStartsSites(): void
    {
        $resident = (string) file_get_contents(
            dirname(__DIR__, 2).'/scripts/ezs_supervisor_resident.ps1'
        );
        self::assertStringNotContainsString('-Action Boot', $resident);
        self::assertStringNotContainsString('ezs_boot_sites_r7.ps1', $resident);
        self::assertStringNotContainsString('Start-Process', $resident);
    }

    public function testDevModeRestrictedAndNoProcessMutation(): void
    {
        self::assertTrue(DevWebModeController::allowed('dev', 'localhost', '127.0.0.1'));
        self::assertFalse(DevWebModeController::allowed('prod', 'localhost', '127.0.0.1'));
        self::assertFalse(DevWebModeController::allowed('dev', 'example.com', '127.0.0.1'));
        $src = (string) file_get_contents(
            dirname(__DIR__, 2).'/src/Module/Infrastructure/Controller/DevWebModeController.php'
        );
        self::assertStringNotContainsString('Stop-Process', $src);
        self::assertStringNotContainsString('Start-Process', $src);
        self::assertStringContainsString('dev_mode_not_confirmed', $src);
    }
}
