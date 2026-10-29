<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\GatewayPreflightCommand;
use PHPUnit\Framework\TestCase;

final class GatewayPreflight004Test extends TestCase
{
    private string $fixture;

    protected function setUp(): void
    {
        $this->fixture = rtrim(sys_get_temp_dir(), '/\\') . '/ezs-gateway-phpunit-' . bin2hex(random_bytes(8));
        foreach (['config/caddy', 'runtime_components/prod_gateway_php', 'runtime_components/prod_gateway', 'runtime/v2-prod'] as $part) {
            $path = $this->fixture . '/' . $part;
            if (!mkdir($path, 0700, true) && !is_dir($path)) {
                throw new RuntimeException('EZS_TEST_FIXTURE_CREATE_FAILED');
            }
        }
        file_put_contents($this->fixture . '/config/caddy/Caddyfile.gateway-php-candidate', 'test');
        file_put_contents($this->fixture . '/runtime_components/prod_gateway_php/router.php', '<?php');
        file_put_contents($this->fixture . '/runtime_components/prod_gateway/server.py', 'pass');
        file_put_contents($this->fixture . '/runtime/v2-prod/processes.json', '{}');
    }

    protected function tearDown(): void
    {
        if (!is_dir($this->fixture)) return;
        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($this->fixture, FilesystemIterator::SKIP_DOTS),
            RecursiveIteratorIterator::CHILD_FIRST
        );
        foreach ($iterator as $item) {
            $item->isDir() ? rmdir($item->getPathname()) : unlink($item->getPathname());
        }
        rmdir($this->fixture);
    }

    public function testCandidateDoesNotAuthorizeProdCutover(): void
    {
        $result = GatewayPreflightCommand::candidate($this->fixture, static fn(): array => ['valid' => true, 'error' => '']);
        self::assertTrue($result['success']);
        self::assertFalse($result['data']['prod_cutover_authorized']);
    }

    public function testCutoverPreflightReportsValidGatewayWithoutAuthorizingCutover(): void
    {
        $payload = ['protocol' => 'ezscore.online-gateway.v3', 'ok' => true, 'backend_port' => 8511, 'maintenance' => true];
        $result = GatewayPreflightCommand::cutover(
            $this->fixture,
            static fn(string $uri): array => ['http' => 200, 'body' => json_encode($payload, JSON_THROW_ON_ERROR)]
        );
        self::assertTrue($result['success']);
        self::assertFalse($result['data']['can_cutover']);
        self::assertTrue($result['data']['prod_maintenance']);
    }

    public function testCutoverPreflightRejectsUnavailableGateway(): void
    {
        $result = GatewayPreflightCommand::cutover(
            $this->fixture,
            static fn(string $uri): array => ['http' => 503, 'body' => null]
        );
        self::assertFalse($result['success']);
        self::assertFalse($result['data']['can_cutover']);
    }
}
