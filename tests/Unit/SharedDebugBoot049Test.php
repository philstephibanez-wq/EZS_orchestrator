<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugBoot049Test extends TestCase
{
    public function testVersionedDevAssetAndExplicitInitializationState(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');

        self::assertStringContainsString('ezs-dev-debug.js?v={{ orchestrator_version|url_encode }}', $layout);
        self::assertStringContainsString('Diagnostic non initialisé', $layout);
        self::assertStringContainsString("panel.dataset.ezsDebugReady = '1'", $script);
        self::assertStringContainsString("status.textContent = 'Diagnostic prêt'", $script);
        self::assertStringContainsString("if (panel.open) void collect()", $script);
        self::assertStringContainsString("spinner.classList.remove('d-none')", $script);
        self::assertStringNotContainsString('Ouvrir le volet pour recueillir les états', $layout);
        self::assertSame(0, preg_match('/\bmethod\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\']/i', $script));
    }
}
