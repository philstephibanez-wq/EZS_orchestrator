<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootWatchdogDevSafetyContractTest extends TestCase
{
    public function testDevDoesNotKillIdentifiedCaddyOnlyBecauseHttpTimesOut(): void
    {
        $root=dirname(__DIR__,2);
        $legacy=file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        $resident=file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        self::assertIsString($legacy);
        self::assertIsString($watchdog);
        self::assertIsString($resident);
        self::assertStringContainsString("throw 'EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP'",$legacy);
        self::assertStringNotContainsString('Stop-Process',$legacy);
        self::assertStringNotContainsString('caddy.exe',$watchdog);
        self::assertStringNotContainsString('8501',$watchdog);
        self::assertStringNotContainsString('8502',$watchdog);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
        self::assertStringContainsString('ROOT_STOP_REFUSED_REATTESTATION',$watchdog);
    }
}
