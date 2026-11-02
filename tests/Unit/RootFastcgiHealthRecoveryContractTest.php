<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiHealthRecoveryContractTest extends TestCase {
    public function testHealthGuardIsScopedAndFailClosed(): void {
        $src=file_get_contents(dirname(__DIR__,2).'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($src);
        foreach (['ROOT_HEALTH_OK','ROOT_HEALTH_FAILED_WAIT_SECONDS=',
            'ROOT_HEALTH_RECOVERY_REFUSED_FOREIGN_LISTENER',
            'ROOT_HEALTH_RECOVERY_REFUSED_NETSTAT_OWNER',
            'ROOT_HEALTH_RECOVERY_REFUSED_INTENT_CHANGED',
            'ROOT_HEALTH_RECOVERY_STOP_PID=',
            'root-fastcgi-recovery.json','ezs.root.health.v1','Stop-Process -Id $targetPid'] as $token) {
            self::assertStringContainsString($token,$src);
        }
        self::assertStringContainsString("Name='prod'",$src);
    }
}
