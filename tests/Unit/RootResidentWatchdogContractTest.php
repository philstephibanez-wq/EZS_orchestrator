<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentWatchdogContractTest extends TestCase {
    public function testResidentUsesOnlyFrankenphpTick(): void {
        $root=dirname(__DIR__,2);
        $resident=file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        self::assertStringContainsString('ezs_root_frankenphp_watchdog.ps1',$resident);
        self::assertStringContainsString('& $watchdog -Once',$resident);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON',$resident);
        self::assertStringContainsString('ROOT_HEALTHY_UNMANAGED_NO_ADOPTION',$watchdog);
        self::assertStringContainsString('ROOT_INTENTION_STOPPED_NO_ACTION',$watchdog);
        self::assertStringContainsString('ROOT_REFUSED_FOREIGN_LISTENER',$watchdog);
        self::assertStringContainsString('ROOT_STOP_REFUSED_REATTESTATION',$watchdog);
        self::assertStringNotContainsString('php-cgi.exe',$watchdog);
        self::assertStringNotContainsString('caddy.exe',$watchdog);
        self::assertStringNotContainsString('--worker',$watchdog);
    }
}
