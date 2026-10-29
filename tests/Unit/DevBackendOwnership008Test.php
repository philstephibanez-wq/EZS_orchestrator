<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\DevBackendOwnership;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

final class DevBackendOwnership008Test extends TestCase
{
    public static function cases(): iterable
    {
        $valid = [
            'ProcessId' => 1234,
            'ExecutablePath' => 'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
            'CommandLine' => '"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8602',
        ];
        yield 'valide' => ['owned_signature', 1234, $valid];
        yield 'pid zero' => ['unknown', 0, $valid];
        yield 'pid different' => ['foreign', 5678, $valid];
        yield 'port prefixe' => ['foreign', 1234, [...$valid, 'CommandLine' => 'php-cgi.exe -b 127.0.0.1:86020']];
        yield 'binaire etranger' => ['foreign', 1234, [...$valid, 'ExecutablePath' => 'C:\\other\\php-cgi.exe']];
    }

    #[DataProvider('cases')]
    public function testClassification(string $expected, int $pid, array $process): void
    {
        self::assertSame($expected, DevBackendOwnership::classify($pid, $process));
    }

    public function testPidZeroNotRead(): void
    {
        self::assertNull(DevBackendOwnership::processByPid(0));
    }
}
