<?php

declare(strict_types=1);
use PHPUnit\Framework\TestCase;

final class SiteBootR7ContractTest extends TestCase
{
    public function testRetiredBootCannotStartAnyProcess(): void
    {
        $root=dirname(__DIR__,2);
        $boot=(string) file_get_contents($root.'/scripts/ezs_boot_sites_r7.ps1');
        self::assertStringContainsString('EZS_R9_SITE_BOOT_RETIRED_USE_WINDOWS_SERVICE',$boot);
        self::assertStringContainsString('web-hard-ping',$boot);
        self::assertStringNotContainsString('Start-Process',$boot);
        self::assertStringNotContainsString('Stop-Process',$boot);
        self::assertStringNotContainsString('ezs_platform_control',$boot);
    }

    public function testResidentNoLongerBootsAnySite(): void
    {
        $resident=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringNotContainsString('ezs_boot_sites_r7.ps1',$resident);
        self::assertStringNotContainsString('-Action Boot',$resident);
        self::assertStringContainsString('$watchdog -Once',$resident);
    }
}
