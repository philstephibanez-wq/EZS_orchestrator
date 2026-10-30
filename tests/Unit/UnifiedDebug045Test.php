<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class UnifiedDebug045Test extends TestCase
{
    public function testSingleSharedDiagnosticAndJsonNativeReadOnlyEndpoint(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        $controller = (string) file_get_contents($root.'/src/Module/Infrastructure/Controller/DevGroupDebugController.php');
        self::assertStringContainsString('id="ezs-debug-native"', $layout);
        self::assertStringContainsString('id="ezs-debug-groups-body"', $layout);
        self::assertStringContainsString('Copier le diagnostic complet', $layout);
        self::assertStringNotContainsString('href="/debug/dev-groups"', $layout);
        self::assertStringContainsString('/api/v2/infrastructure/dev-debug-native', $js);
        self::assertStringContainsString('/api/v2/infrastructure/dev-groups', $js);
        self::assertStringContainsString('nativeNames', $js);
        self::assertStringNotContainsString("method:'POST'", $js);
        self::assertStringContainsString("methods: ['GET']", $controller);
        self::assertStringNotContainsString("#[Route('/debug/dev-groups'", $controller);
        self::assertStringContainsString('INVENTORY_UNAVAILABLE', $controller);
    }
}
