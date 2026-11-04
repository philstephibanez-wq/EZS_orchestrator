<?php

declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\DevWebModeController;
use PHPUnit\Framework\TestCase;

/** Contract for the unified (not legacy native) DEV maintenance configuration. */
final class DevNativeMaintenanceR9FTest extends TestCase
{
    private static function configuration(): string
    {
        $path = dirname(__DIR__, 2).'/config/frankenphp/Caddyfile.platform.unified';
        self::assertFileExists($path);
        $content = file_get_contents($path);
        self::assertNotFalse($content);
        return $content;
    }

    private static function listener(string $content, int $port): void
    {
        self::assertSame(
            1,
            preg_match('/^\\s*:' . $port . '\\s*\\{\\s*$/m', $content),
            sprintf('Listener %d absent ou non declare dans le Caddyfile unifie', $port)
        );
    }

    public function testUnifiedDevUsesSameMaintenanceMarkerAsControllerAndPlatform(): void
    {
        $conf = self::configuration();
        self::listener($conf, 8502);
        self::listener($conf, 8602);
        self::assertStringContainsString('bind 127.0.0.1', $conf);
        self::assertStringContainsString('try_files dev.maintenance', $conf);
        self::assertStringContainsString('root H:/EZS_orchestrator/runtime/web-modes', $conf);
        self::assertStringContainsString('header Retry-After "120"', $conf);
        self::assertStringContainsString('503', $conf);
        self::assertStringContainsString('forward_auth 127.0.0.1:8602', $conf);
        self::assertStringContainsString('uri /internal/media/auth', $conf);
        self::assertStringContainsString('root * H:/EZScore_dev/var/storage/stems', $conf);
        self::assertStringContainsString('reverse_proxy 127.0.0.1:8602', $conf);

        $controller = (string) file_get_contents(
            dirname(__DIR__, 2).'/src/Module/Infrastructure/Controller/DevWebModeController.php'
        );
        self::assertStringContainsString('/dev.maintenance', $controller);
        self::assertStringContainsString('runtime/web-modes', $controller);
        self::assertTrue(DevWebModeController::allowed('dev', 'localhost', '127.0.0.1'));
        self::assertFalse(DevWebModeController::allowed('prod', 'localhost', '127.0.0.1'));
        self::assertStringNotContainsString('Stop-Process', $controller);
        self::assertStringNotContainsString('Start-Process', $controller);
    }

    public function testTenLoopbackListenersAreDeclaredOnce(): void
    {
        $conf = self::configuration();
        $ports = [8790, 8502, 8602, 8702, 8701, 8712, 8713, 8501, 8510, 8511];
        foreach ($ports as $port) {
            self::listener($conf, $port);
            self::assertSame(1, preg_match_all('/^\\s*:' . $port . '\\s*\\{\\s*$/m', $conf));
        }
        self::assertSame(10, preg_match_all('/^\\s*:\\d+\\s*\\{\\s*$/m', $conf));
    }

    public function testProdRoutingAndEnvironmentArePreserved(): void
    {
        $conf = self::configuration();
        self::assertStringContainsString('forward_auth 127.0.0.1:8510', $conf);
        self::assertStringContainsString('reverse_proxy 127.0.0.1:8510', $conf);
        self::assertStringContainsString('root * H:/EZScore/var/storage/stems', $conf);
        self::assertStringContainsString('root * H:/EZScore/public', $conf);
        self::assertStringContainsString('root * H:/EZS_orchestrator/runtime_components/prod_gateway_php', $conf);
        self::assertStringContainsString('rewrite * /router.php', $conf);
        self::assertStringContainsString('env APP_ENV prod', $conf);
        self::assertStringContainsString('env APP_DEBUG 0', $conf);
        self::assertStringNotContainsString('php_fastcgi', $conf);
    }
}
