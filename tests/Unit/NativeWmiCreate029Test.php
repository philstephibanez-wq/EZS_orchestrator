<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
final class NativeWmiCreate029Test extends TestCase
{
    public function testProcessCreationNowUsesNativePhpProcOpenWithoutShell():void
    {
        $source=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString('proc_open(', $source);
        self::assertStringContainsString("'bypass_shell' => true", $source);
        self::assertStringNotContainsString('ExecMethod(', $source);
    }
    public function testWmiRemainsForOwnershipAndControlledTermination():void
    {
        $source=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString('Win32_Process.Handle=', $source);
        self::assertStringContainsString('self::attest(', $source);
    }
}
