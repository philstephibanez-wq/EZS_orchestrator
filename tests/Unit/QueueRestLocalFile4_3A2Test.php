<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\QueueRestAccess;
use PHPUnit\Framework\TestCase;

final class QueueRestLocalFile4_3A2Test extends TestCase
{
    public function testReadsOnlyValidUniqueLabToken(): void
    {
        $file = tempnam(sys_get_temp_dir(), 'ezs-token-');
        self::assertIsString($file);
        $token = str_repeat('x', 48);
        try {
            file_put_contents($file, "APP_ENV=dev\nEZS_QUEUE_LAB_TOKEN=\"$token\"\n");
            self::assertSame($token, QueueRestAccess::tokenFromLocalFile($file, 'EZS_QUEUE_LAB_TOKEN'));
            self::assertSame('', QueueRestAccess::tokenFromLocalFile($file, 'EZS_QUEUE_EZSCORE_TOKEN'));
            file_put_contents($file, "EZS_QUEUE_LAB_TOKEN=$token\nEZS_QUEUE_LAB_TOKEN=$token\n");
            self::assertSame('', QueueRestAccess::tokenFromLocalFile($file, 'EZS_QUEUE_LAB_TOKEN'));
            file_put_contents($file, "EZS_QUEUE_LAB_TOKEN=invalid\n");
            self::assertSame('', QueueRestAccess::tokenFromLocalFile($file, 'EZS_QUEUE_LAB_TOKEN'));
            self::assertSame('lab', QueueRestAccess::producerFor('Bearer '.$token, ['lab' => $token]));
            self::assertNull(QueueRestAccess::producerFor('Bearer '.$token, ['lab' => $token, 'assistant' => $token]));
        } finally {
            @unlink($file);
        }
    }
}
