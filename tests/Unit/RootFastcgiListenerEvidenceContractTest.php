<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiListenerEvidenceContractTest extends TestCase
{
    public function testRefusalReportsListenerAndDoesNotWeakenGuard(): void
    {
        $root=dirname(__DIR__,2);
        $watchdog=file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        self::assertIsString($watchdog);
        foreach (['Get-NetTCPConnection -State Listen -ErrorAction Stop',
            'ROOT_REFUSED_FOREIGN_LISTENER','ROOT_REFUSED_AMBIGUOUS_OWNERSHIP',
            'ROOT_REFUSED_PROCESS_WITHOUT_LISTENER','ROOT_STOP_REFUSED_REATTESTATION',
            'ROOT_REFUSED_BOOT_RECHECK'] as $token) {
            self::assertStringContainsString($token,$watchdog);
        }
        self::assertStringContainsString('[int]$ports[0].OwningProcess -ne [int]$all[0].ProcessId',$watchdog);
        self::assertStringNotContainsString('8791',$watchdog);
    }
}
