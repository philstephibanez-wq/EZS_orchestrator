<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiIdentityConsistencyContractTest extends TestCase
{
    public function testBothTerminationPathsAreGuarded(): void
    {
        $root=dirname(__DIR__,2);
        $old=file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        self::assertIsString($old);
        self::assertIsString($watchdog);
        self::assertStringContainsString('EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP',$old);
        self::assertStringNotContainsString('Stop-Process',$old);
        foreach (['Get-RootProcesses','Get-Listeners','Matches-Owner',
            'ROOT_REFUSED_AMBIGUOUS_OWNERSHIP','ROOT_REFUSED_FOREIGN_LISTENER',
            'ROOT_STOP_REFUSED_REATTESTATION','ROOT_REFUSED_PRIOR_PID_STILL_EXISTS',
            'ROOT_REFUSED_BOOT_RECHECK'] as $token) {
            self::assertStringContainsString($token,$watchdog);
        }
        self::assertSame(1,substr_count($watchdog,'Stop-Process -Id ([int]$owner.pid) -Force'));
        $guard=strpos($watchdog,"Log 'ROOT_STOP_REFUSED_REATTESTATION'");
        $kill=strpos($watchdog,'Stop-Process -Id ([int]$owner.pid) -Force');
        self::assertNotFalse($guard);
        self::assertNotFalse($kill);
        self::assertLessThan($kill,$guard);
    }
}
