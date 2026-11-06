<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Yaml\Yaml;
final class MessengerReferenceConsistencyTest extends TestCase
{
    public function testReferenceDocumentsEnabledMessenger(): void
    {
        $root=dirname(__DIR__,2);
        $yaml=Yaml::parseFile($root.'/config/packages/messenger.yaml');
        self::assertSame(['global_queue'],array_keys($yaml['framework']['messenger']['transports']));
        self::assertSame([],$yaml['framework']['messenger']['routing']);
        $reference=file_get_contents($root.'/config/reference.php');
        self::assertIsString($reference);
        self::assertSame(1,preg_match('/messenger\?: bool\|array\{[^\r\n]*\R\s*\*\s*enabled\?: bool\|Param, \/\/ Default: true/',$reference));
    }
}
