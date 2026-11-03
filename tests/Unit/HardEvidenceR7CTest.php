<?php

declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class HardEvidenceR7CTest extends TestCase
{
    public function testHardStatusUsesExistingTcpHttpCollector(): void
    {
        $root=dirname(__DIR__,2);
        $adapter=(string)file_get_contents($root.'/scripts/ezs_boot_sites_r7.ps1');
        $collector=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/WebHardPingController.php');
        self::assertStringContainsString('web-hard-ping',$adapter);
        self::assertStringContainsString('stream_socket_client',$collector);
        self::assertStringContainsString('file_get_contents($url',$collector);
        self::assertStringNotContainsString('Get-CimInstance',$adapter);
        self::assertStringNotContainsString('Start-Process',$adapter);
    }
}
