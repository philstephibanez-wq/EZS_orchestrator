<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use PHPUnit\Framework\TestCase;

final class QueueDiagnostic4_3A14Test extends TestCase
{
    public function testQueueDiagnosticIsReadOnlyAndRedacted(): void
    {
        $root = dirname(__DIR__, 2);
        $controller = file_get_contents($root.'/src/Module/Coordination/Controller/QueueDiagnosticController.php');
        $js = file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertIsString($controller);
        self::assertIsString($js);
        self::assertStringContainsString('mode=ro', $controller);
        self::assertStringContainsString('PRAGMA query_only=ON', $controller);
        self::assertStringContainsString('dev_loopback_only', $controller);
        self::assertStringNotContainsString('lease_token', $controller);
        self::assertStringNotContainsString('e.message', $controller);
        self::assertStringContainsString('/api/v2/queue/dev-diagnostic', $js);
    }
}
