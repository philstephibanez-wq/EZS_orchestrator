<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\QueueExecutorAccess;
use PHPUnit\Framework\TestCase;

final class QueueExecutorLocalEnv4_3A6Test extends TestCase
{
    public function testExplicitAllowlistedFallbackRejectsDuplicatesAndBadValues(): void
    {
        $path = tempnam(sys_get_temp_dir(), 'ezs-executor-env-');
        self::assertIsString($path);
        try {
            file_put_contents($path, "EZS_QUEUE_EXECUTOR_API=1\nEZS_QUEUE_EXECUTOR_TOKEN=".str_repeat('a',64)."\n");
            self::assertSame('1', QueueExecutorAccess::localSetting($path, 'EZS_QUEUE_EXECUTOR_API'));
            self::assertSame(str_repeat('a',64), QueueExecutorAccess::localSetting($path, 'EZS_QUEUE_EXECUTOR_TOKEN'));
            self::assertSame('', QueueExecutorAccess::localSetting($path, 'EZS_QUEUE_LAB_TOKEN'));
            file_put_contents($path, "EZS_QUEUE_EXECUTOR_API=1\nEZS_QUEUE_EXECUTOR_API=0\n");
            self::assertSame('', QueueExecutorAccess::localSetting($path, 'EZS_QUEUE_EXECUTOR_API'));
            file_put_contents($path, "EZS_QUEUE_EXECUTOR_API=maybe\n");
            self::assertSame('', QueueExecutorAccess::localSetting($path, 'EZS_QUEUE_EXECUTOR_API'));
        } finally {
            @unlink($path);
        }
    }
}
