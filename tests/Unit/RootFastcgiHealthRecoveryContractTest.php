<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiHealthRecoveryContractTest extends TestCase {
    public function testHealthGuardIsScopedAndFailClosed(): void {
        $root=dirname(__DIR__,2);
        $legacy=file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        self::assertIsString($legacy);
        self::assertIsString($watchdog);
        self::assertStringContainsString("throw 'EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP'",$legacy);
        self::assertStringNotContainsString('Start-Process',$legacy);
        foreach (['http://127.0.0.1:8790/health','ezs.root.health.v1',
            'ROOT_INTENTION_STOPPED_NO_ACTION','ROOT_HEALTHY_OWNED',
            'ROOT_HEALTHY_UNMANAGED_NO_ADOPTION','ROOT_HEALTH_FAILED_WAIT',
            'ROOT_STOP_REFUSED_REATTESTATION','ROOT_REFUSED_FOREIGN_LISTENER'] as $token) {
            self::assertStringContainsString($token,$watchdog);
        }
        self::assertStringNotContainsString('php-cgi.exe',$watchdog);
        self::assertStringNotContainsString('caddy.exe',$watchdog);
    }
}
