<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class FrankenphpDevServiceContractTest extends TestCase
{
    public function testDevServiceCannotStartDuringProvisioning(): void
    {
        $script = file_get_contents(__DIR__ . '/../../scripts/ezs_frankenphp_dev_service.ps1');
        self::assertIsString($script);
        self::assertStringContainsString("'InstallDisabled'", $script);
        self::assertStringContainsString('Set-Service -Name $serviceName -StartupType Disabled', $script);
        self::assertStringNotContainsString('Start-Service', $script);
        self::assertStringNotContainsString('Stop-Process', $script);
        self::assertStringContainsString("'ROOT_WATCHDOG_PRESENT'", $script);
        self::assertStringContainsString("'SERVICE_OWNERSHIP_OR_STATE_REFUSED'", $script);
    }
}
