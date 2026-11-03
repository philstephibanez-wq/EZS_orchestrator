<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class LegacyFastCgiSupervisorRetirementContractTest extends TestCase
{
    public function testRemovedSupervisorCannotStartOrStopLegacyProcess(): void
    {
        $root = dirname(__DIR__, 2);
        $source = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($source);
        self::assertStringContainsString('EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP', $source);
        self::assertStringContainsString('throw ', $source);
        foreach (['Start-Process', 'Stop-Process', 'php-cgi.exe', 'php_fastcgi', 'Start-RootFastCgi', 'Start-Caddy'] as $forbidden) {
            self::assertStringNotContainsString($forbidden, $source);
        }
        $native = file_get_contents($root.'/scripts/ezs_native_site.ps1');
        self::assertIsString($native);
        self::assertStringContainsString('frankenphp.exe', $native);
        self::assertStringContainsString('NATIVE_CONFIG_LEGACY_FASTCGI_REFUSED', $native);
    }
}
