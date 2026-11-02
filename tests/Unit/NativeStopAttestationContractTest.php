<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeStopAttestationContractTest extends TestCase
{
    public function testStopUsesBoundedNativePidTerminationAndWaitsForExit(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertIsString($source);
        self::assertStringContainsString("'C:/Windows/System32/taskkill.exe', '/PID'", $source);
        self::assertStringContainsString('EZS_FASTCGI_STOP_NOT_EXITED_', $source);
        self::assertStringContainsString('!isset($afterProcesses[$pid]) && !self::occupied($spec, $afterPorts)', $source);
        self::assertStringContainsString('EZS_FASTCGI_IDENTITY_CHANGED_', $source);
    }

    public function testHttpStopRequiresNativeStoppedAttestation(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertIsString($source);
        self::assertStringContainsString("'EZS_STOP_NOT_VERIFIED_'", $source);
        self::assertStringContainsString("'group_stop_verified'", $source);
        self::assertStringContainsString("'restart_incomplete'", $source);
    }
}
