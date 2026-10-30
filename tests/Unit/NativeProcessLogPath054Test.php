<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeProcessLogPath054Test extends TestCase
{
    public function testPersistentNativeLogPathAndSafeUnchangedSpawnSemantics(): void
    {
        $root = dirname(__DIR__, 2);
        $source = (string) file_get_contents($root.'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString("self::ROOT.'/var/log/native'", $source);
        self::assertStringNotContainsString('H:/temp/ezs-orchestrator/native-proc-open', $source);
        self::assertStringContainsString("'EZS_PROC_LOG_DIR_NOT_WRITABLE'", $source);
        self::assertStringContainsString("0 => ['file', 'NUL', 'r']", $source);
        self::assertStringContainsString("'.out.log', 'a'", $source);
        self::assertStringContainsString("'.err.log', 'a'", $source);
        self::assertStringContainsString("'bypass_shell' => true", $source);
        self::assertStringContainsString('self::$spawnHandles[] = $resource', $source);
        self::assertStringNotContainsString('unlink($logDir', $source);
    }
}
