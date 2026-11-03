<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiRecoverySafetyContractTest extends TestCase {
    public function testRecoveryIsExplicitlyGuarded(): void {
        $root=dirname(__DIR__,2);
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        $resident=file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        self::assertIsString($watchdog);
        self::assertIsString($resident);
        foreach (['ezs.desired-services.v1','ROOT_INTENT_INVALID','Matches-Owner',
            'ROOT_INTENTION_STOPPED_NO_ACTION','ROOT_HEALTH_FAILED_WAIT','ROOT_UNHEALTHY_WAIT',
            'ROOT_UNHEALTHY_STALE_REFUSED','ROOT_STOP_REFUSED_REATTESTATION',
            'ROOT_RESTART_BACKOFF','ROOT_REFUSED_PRIOR_PID_STILL_EXISTS',
            'ROOT_BOOT_HTTP_PENDING','ROOT_RECOVERED_HTTP_OK'] as $token) {
            self::assertStringContainsString($token,$watchdog);
        }
        self::assertStringContainsString('EZS_ROOT_FRANKENPHP_TICK',$watchdog);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON',$resident);
        self::assertStringContainsString('ezs_root_frankenphp_watchdog.ps1',$resident);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
    }
}
