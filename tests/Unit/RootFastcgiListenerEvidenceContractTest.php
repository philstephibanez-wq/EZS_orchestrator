<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiListenerEvidenceContractTest extends TestCase
{
    public function testRefusalReportsListenerAndDoesNotWeakenGuard(): void
    {
        $root = dirname(__DIR__, 2);
        $watchdog = (string) file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        $resident = (string) file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringContainsString('ROOT_WEB_REACHABLE', $watchdog);
        self::assertStringContainsString('ROOT_WEB_UNAVAILABLE', $watchdog);
        self::assertStringContainsString('http://127.0.0.1:8790/', $watchdog);
        self::assertStringContainsString('EZS_ROOT_FRANKENPHP_TICK', $watchdog);
        self::assertStringNotContainsString('Stop-Process', $watchdog);
        self::assertStringNotContainsString('Start-Process', $watchdog);
        self::assertStringNotContainsString('Get-CimInstance', $watchdog);
        self::assertStringNotContainsString('Get-RootProcesses', $watchdog);
        self::assertStringNotContainsString('ezs_boot_sites_r7.ps1', $resident);
        self::assertStringNotContainsString('-Action Boot', $resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON', $resident);
    }
}
