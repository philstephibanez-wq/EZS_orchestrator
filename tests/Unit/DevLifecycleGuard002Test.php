<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\EcosystemLifecycleGuard;
use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;
use PHPUnit\Framework\TestCase;

final class DevLifecycleGuard002Test extends TestCase
{
    private string $directory;

    protected function setUp(): void
    {
        $this->directory = 'H:/temp/ezs-phpunit-lifecycle-' . bin2hex(random_bytes(8));
        foreach (['runtime/v2-dev', 'runtime/v2-prod'] as $sub) {
            if (!mkdir($this->directory . '/' . $sub, 0700, true)) {
                throw new RuntimeException('EZS_TEST_FIXTURE_FAILED');
            }
        }
    }

    protected function tearDown(): void
    {
        if (!is_dir($this->directory)) return;
        $iter = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($this->directory, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($iter as $item) $item->isDir() ? rmdir($item->getPathname()) : unlink($item->getPathname());
        rmdir($this->directory);
    }

    public function testOnlyStaleDevStateIsRemovedAndProdStateIsUntouched(): void
    {
        $dev = $this->directory . '/runtime/v2-dev/processes.json';
        $prod = $this->directory . '/runtime/v2-prod/processes.json';
        file_put_contents($dev, '{"php_pid":12345,"caddy_pid":12346}');
        file_put_contents($prod, '{"gateway_pid":98765}');
        $runs = 0;
        $inventory = new WindowsProcessInventory(static function () use (&$runs): iterable { ++$runs; return []; });
        $cleaned = (new EcosystemLifecycleGuard())->cleanupDevStale($this->directory, $inventory, static fn(int $port): bool => false);
        self::assertSame(1, $cleaned);
        self::assertSame(2, $runs);
        self::assertFileDoesNotExist($dev);
        self::assertSame('{"gateway_pid":98765}', file_get_contents($prod));
    }

    public function testActiveDevListenerRefusesCleanupAndPreservesState(): void
    {
        $dev = $this->directory . '/runtime/v2-dev/processes.json';
        file_put_contents($dev, '{"php_pid":12345}');
        try {
            (new EcosystemLifecycleGuard())->cleanupDevStale(
                $this->directory,
                new WindowsProcessInventory(static fn(): iterable => []),
                static fn(int $port): bool => $port === 8791
            );
            self::fail('An active DEV port must block cleanup');
        } catch (RuntimeException $e) {
            self::assertStringContainsString('PORT_ACTIVE', $e->getMessage());
            self::assertFileExists($dev);
        }
    }
}
