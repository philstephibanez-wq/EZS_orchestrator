<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use PHPUnit\Framework\TestCase;
use Symfony\Component\Yaml\Yaml;

final class MessengerBootstrapContractTest extends TestCase
{
    public function testMessengerBootstrapHasNoTransportOrRouting(): void
    {
        self::assertTrue(class_exists(\Symfony\Component\Messenger\MessageBus::class));
        $path = dirname(__DIR__, 2) . '/config/packages/messenger.yaml';
        $configuration = Yaml::parseFile($path);
        self::assertIsArray($configuration);
        self::assertSame([], $configuration['framework']['messenger']['transports']);
        self::assertSame([], $configuration['framework']['messenger']['routing']);
    }
}
