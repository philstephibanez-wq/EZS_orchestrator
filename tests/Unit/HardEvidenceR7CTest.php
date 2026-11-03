<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class HardEvidenceR7CTest extends TestCase
{
    public function testWebHardPingUsesTcpAndHttpWithoutPidOrRestHealth():void
    {
        $src=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_boot_sites_r7.ps1');
        self::assertStringContainsString('Get-NetTCPConnection -State Listen',$src);
        self::assertStringContainsString('Web-Http',$src);
        self::assertStringContainsString("'HardStatus'",$src);
        self::assertStringContainsString('EZS_R8_WEB_INCOMPLETE_',$src);
        self::assertStringNotContainsString('HARD_SITE=',$src);
        self::assertStringNotContainsString('Get-CimInstance',$src);
        self::assertStringNotContainsString('Stop-Process',$src);
    }
}
