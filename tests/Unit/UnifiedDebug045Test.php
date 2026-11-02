<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class UnifiedDebug045Test extends TestCase
{
    public function testSingleSharedRawJsonDiagnosticAndReadOnlyEndpoint(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        $controller = (string) file_get_contents($root.'/src/Module/Infrastructure/Controller/DevGroupDebugController.php');
        self::assertStringContainsString('id="ezs-debug-output"', $layout);
        self::assertStringNotContainsString('id="ezs-debug-groups-body"', $layout);
        self::assertStringNotContainsString('id="ezs-debug-native"', $layout);
        self::assertStringContainsString('Copier le diagnostic complet', $layout);
        self::assertStringContainsString('/api/v2/infrastructure/dev-debug-native', $js);
        self::assertStringContainsString('/api/v2/infrastructure/dev-groups', $js);
        self::assertStringContainsString('/api/v2/infrastructure/dev-health', $js);
        self::assertStringContainsString('/api/v2/infrastructure/dev-backend', $js);
        self::assertStringContainsString('JSON.stringify(snapshot,null,2)', $js);
        self::assertStringContainsString("request:{method:'POST'", $js);
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $js);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $js);
        self::assertStringContainsString("ezsActionStarted.get(xhr)", $js);
        self::assertStringContainsString("methods: ['GET']", $controller);
        self::assertStringContainsString('INVENTORY_UNAVAILABLE', $controller);
    }
}
