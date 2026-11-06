<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Yaml\Yaml;
final class MessengerBootstrapContractTest extends TestCase
{
    public function testMessengerHasExactlyOneCanonicalTransport(): void
    {
        self::assertTrue(class_exists(\Symfony\Component\Messenger\MessageBus::class));
        $config=Yaml::parseFile(dirname(__DIR__,2).'/config/packages/messenger.yaml');
        self::assertSame(['global_queue'],array_keys($config['framework']['messenger']['transports']));
        self::assertSame('ezs-global://local',$config['framework']['messenger']['transports']['global_queue']['dsn']);
        self::assertSame(0,$config['framework']['messenger']['transports']['global_queue']['retry_strategy']['max_retries']);
        self::assertSame([],$config['framework']['messenger']['routing']);
    }
}
