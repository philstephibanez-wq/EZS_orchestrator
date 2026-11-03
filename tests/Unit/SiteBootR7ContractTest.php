<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SiteBootR7ContractTest extends TestCase
{
    public function testSingleWebBootAndNoIndividualServiceCommands():void
    {
        $root=dirname(__DIR__,2);
        $boot=(string)file_get_contents($root.'/scripts/ezs_boot_sites_r7.ps1');
        self::assertStringContainsString("@('dev','lab','assistant','prod')",$boot);
        self::assertStringContainsString('SKIPPED_PROD_MAINTENANCE',$boot);
        self::assertStringContainsString('BLOCKED_PARTIAL',$boot);
        self::assertStringContainsString('Start-Process -FilePath $exe',$boot);
        self::assertStringContainsString('http://127.0.0.1:8502/fr/catalog',$boot);
        self::assertStringContainsString('http://127.0.0.1:8712/',$boot);
        self::assertStringNotContainsString('Get-CimInstance',$boot);
        self::assertStringNotContainsString('OwningProcess',$boot);
        self::assertStringNotContainsString('Stop-Process',$boot);
        self::assertStringNotContainsString('desired-services.json',$boot);
    }
    public function testResidentStillBootsOnlyOnceAfterRootHealth():void
    {
        $script=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringContainsString('if (!$attempted)',$script);
        self::assertStringContainsString('$attempted=$true',$script);
        self::assertStringContainsString('127.0.0.1:8790/health',$script);
        self::assertStringContainsString('-Action Boot',$script);
    }
}
