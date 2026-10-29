<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class NativeHiddenStartup030Test extends TestCase
{
    public function testProcessCreationDoesNotAskWindowsForNewConsole():void
    {
        $source=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString("'create_new_console' => false", $source);
        self::assertStringContainsString("'bypass_shell' => true", $source);
        self::assertStringContainsString("'file', \$logDir", $source);
    }
}
