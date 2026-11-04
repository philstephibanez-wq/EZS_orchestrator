<?php

declare(strict_types=1);

namespace Ezs\Tests\Unit;

use Ezs\Web\Module\Coordination\QueueRestAccess;
use PHPUnit\Framework\TestCase;

final class QueueRestSymfonyEnv4_3A1Test extends TestCase
{
    public function testSymfonyServerEnvironmentIsAcceptedWithoutPutenv(): void
    {
        $key = 'EZS_QUEUE_LAB_TOKEN';
        $oldNative = getenv($key);
        $oldServer = $_SERVER[$key] ?? null;
        $oldEnv = $_ENV[$key] ?? null;
        $token = str_repeat('a', 48);
        try {
            putenv($key);
            unset($_ENV[$key]);
            $_SERVER[$key] = $token;
            self::assertSame('lab', QueueRestAccess::producerFor('Bearer '.$token));
            $_SERVER[$key] = 'wrong-value';
            self::assertNull(QueueRestAccess::producerFor('Bearer '.$token));
            unset($_SERVER[$key]);
            $_ENV[$key] = $token;
            self::assertSame('lab', QueueRestAccess::producerFor('Bearer '.$token));
            self::assertNull(QueueRestAccess::producerFor('Bearer '.str_repeat('b', 48)));
        } finally {
            $oldNative === false ? putenv($key) : putenv($key.'='.$oldNative);
            if ($oldServer === null) { unset($_SERVER[$key]); } else { $_SERVER[$key] = $oldServer; }
            if ($oldEnv === null) { unset($_ENV[$key]); } else { $_ENV[$key] = $oldEnv; }
        }
    }
}
