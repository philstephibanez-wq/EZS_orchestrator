<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeWmiCreate029Test extends TestCase
{
    public function testProcessCreationUsesNativePhpProcOpenWithoutShell(): void
    {
        $source = (string) file_get_contents(dirname(__DIR__, 2) . '/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString('proc_open(', $source);
        self::assertStringContainsString("'bypass_shell' => true", $source);
        self::assertStringNotContainsString('ExecMethod(', $source);
    }

    public function testTerminationUsesNativeWindowsToolAfterOwnershipAttestation(): void
    {
        $source = (string) file_get_contents(dirname(__DIR__, 2) . '/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString('function nativeTerminate(int $pid)', $source);
        self::assertStringContainsString('C:/Windows/System32/taskkill.exe', $source);
        self::assertStringContainsString("'/PID'", $source);
        self::assertStringContainsString("'/F'", $source);
        self::assertStringContainsString('self::attest(', $source);
        self::assertStringContainsString('EZS_FASTCGI_STOP_NOT_EXITED_', $source);
        self::assertStringNotContainsString('Win32_Process.Handle=', $source);
    }
}
