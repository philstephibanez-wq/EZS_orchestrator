<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class DevAppsRecovery023Test extends TestCase {
    private static function content(string $name): string {
        return (string)file_get_contents(dirname(__DIR__, 2).'/scripts/'.$name.'.ps1');
    }
    public function testBothEntrypointsContainActualRecovery(): void {
        foreach (['start','stop'] as $entry) {
            $s=self::content($entry);
            self::assertSame(1, substr_count($s, '# EZS_DEV_APPS_RECOVERY_R8'));
            self::assertStringContainsString('EZS_R8_DEV_APP_STALE_RECOVERY_OK', $s);
            self::assertStringContainsString('stale-dev-apps', $s);
        }
    }
    public function testLiveRecordedPidsMustRefuseBeforeArchiving(): void {
        foreach (['start','stop'] as $entry) {
            $s=self::content($entry);
            $position=strpos($s,'# EZS_DEV_APPS_RECOVERY_R8');
            self::assertNotFalse($position);
            $block=substr($s,$position,4200);
            self::assertStringContainsString('Get-CimInstance Win32_Process', $block);
            self::assertStringContainsString('EZS_R8_DEV_RECOVERY_REFUSED_RECORDED_PID_ACTIVE_', $block);
            self::assertLessThan(strpos($block,'Move-Item -LiteralPath $stateFile'),strpos($block,'RECOVERY_REFUSED_RECORDED_PID_ACTIVE_'));
        }
    }
    public function testPortOwnershipMustBeAbsentAcrossTwoPasses(): void {
        foreach(['start','stop'] as $entry) {
            $s=self::content($entry);
            $block=substr($s,(int)strpos($s,'# EZS_DEV_APPS_RECOVERY_R8'),4200);
            self::assertStringContainsString('$ezsR8Pass -le 2',$block);
            self::assertStringContainsString('Get-NetTCPConnection -State Listen -ErrorAction Stop',$block);
            self::assertStringContainsString('8602,8862',$block);
            self::assertStringContainsString('EZS_R8_DEV_RECOVERY_REFUSED_PORT_ACTIVE_',$block);
        }
    }
    public function testNoProdOrProcessTerminationInGuard():void {
        foreach(['start','stop'] as $entry) {
            $s=self::content($entry);
            $block=substr($s,(int)strpos($s,'# EZS_DEV_APPS_RECOVERY_R8'));
            $block=explode('    if(Test-Path -LiteralPath $stateFile)', $block,2)[0];
            self::assertStringNotContainsString('Stop-Process',$block);
            self::assertStringNotContainsString('v2-prod',$block);
            self::assertStringNotContainsString('Remove-Item -LiteralPath $stateFile',$block);
        }
    }
}
