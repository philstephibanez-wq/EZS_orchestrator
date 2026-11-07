<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use PHPUnit\Framework\TestCase;

final class GlobalQueueJobHandler4_3A17Test extends TestCase
{
    public function testBridgeFailuresAreCategorizedWithoutRawChildOutput(): void
    {
        $path = dirname(__DIR__, 2).'/src/Module/Coordination/Messenger/GlobalQueueJobHandler.php';
        self::assertFileExists($path);
        $source = file_get_contents($path);
        self::assertIsString($source);
        self::assertStringContainsString('LAB_GLOBAL_PROFILE_STATE=', $source);
        self::assertStringContainsString('LAB_GLOBAL_PROFILE_EXECUTION_FAILED:', $source);
        self::assertStringNotContainsString('$process->disableOutput()', $source);
        self::assertStringNotContainsString('throw new \\RuntimeException($result)', $source);
        $receiver = dirname(__DIR__, 2).'/src/Module/Coordination/Messenger/GlobalQueueReceiver.php';
        self::assertStringContainsString("getenv('EZS_QUEUE_RECOVERY_ONLY')", (string) file_get_contents($receiver));
    }
}
