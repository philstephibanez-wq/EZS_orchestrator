<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class FrankenphpCanonicalServiceContractTest extends TestCase {
    public function testCanonicalServiceIsNotDevOrProdAndDoesNotStartImplicitly(): void {
        $base = dirname(__DIR__, 2);
        $xml = simplexml_load_file($base.'/config/frankenphp/EZS_FrankenPHP.xml');
        self::assertNotFalse($xml);
        self::assertSame('EZS_FrankenPHP', (string) $xml->id);
        self::assertSame('Manual', (string) $xml->startmode);
        self::assertStringContainsString('127.0.0.1:8790', (string) $xml->arguments);
        self::assertStringNotContainsString('worker', (string) $xml->arguments);
        $ps = file_get_contents($base.'/scripts/ezs_frankenphp_service_rename.ps1');
        self::assertNotFalse($ps);
        self::assertStringContainsString('CANONICAL_INSTALLED_DISABLED_OLD_STOPPED', $ps);
        self::assertStringContainsString("State -ne 'Stopped'", $ps);
        self::assertStringContainsString('ROOT_LISTENER_PRESENT_REFUSED', $ps);
        self::assertStringContainsString('FRANKENPHP_PROCESS_PRESENT_REFUSED', $ps);
        self::assertStringNotContainsString('Invoke-RestMethod', $ps);
        self::assertStringNotContainsString('Stop-Service -Name $old', $ps);
        self::assertStringNotContainsString('Start-Service -Name $name', $ps);
    }
}
