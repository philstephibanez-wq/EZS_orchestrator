<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class HardEvidenceR7CTest extends TestCase {
    public function testHardStatusMustRejectUnverifiedSites(): void {
        $src=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_boot_sites_r7.ps1');
        self::assertStringContainsString('HARD_SITE=', $src);
        self::assertStringContainsString("\$before.state -ne 'RUNNING'", $src);
        self::assertStringContainsString('EZS_R7_HARD_EVIDENCE_MISSING_', $src);
        self::assertStringContainsString('reason=', $src);
        self::assertStringNotContainsString('Stop-Process',$src);
    }
    public function testNoSyntheticActualProcessCountsAndPidOwnershipEvidence(): void {
        $src=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_native_site.ps1');
        self::assertStringContainsString('PROCESSES=$actual',$src);
        self::assertStringContainsString('$listener.OwningProcess',$src);
        self::assertStringContainsString('OWNER_RECORD_MISSING',$src);
        self::assertStringContainsString('HARD_ATTESTED',$src);
        self::assertStringContainsString('PROCESS_IDENTITY_REATTEST_FAILED',$src);
    }
}
