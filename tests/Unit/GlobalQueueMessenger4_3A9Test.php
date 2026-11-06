<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class GlobalQueueMessenger4_3A9Test extends TestCase
{
    public function testTransportIsReceiverOnlyAndFifo(): void
    {
        $source = file_get_contents(__DIR__.'/../../src/Module/Coordination/Messenger/GlobalQueueReceiver.php');
        self::assertIsString($source);
        self::assertStringContainsString('ORDER BY created_at,id LIMIT 1', $source);
        self::assertStringContainsString("state='running'", $source);
        self::assertStringContainsString('flock($lock, LOCK_EX | LOCK_NB)', $source);
    }

    public function testMessengerUsesOneCanonicalTransport(): void
    {
        $source = file_get_contents(__DIR__.'/../../config/packages/messenger.yaml');
        self::assertIsString($source);
        self::assertStringContainsString('ezs-global://local', $source);
        self::assertStringContainsString('max_retries: 0', $source);
    }
}
