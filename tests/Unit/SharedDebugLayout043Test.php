<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugLayout043Test extends TestCase
{
    public function testSharedDevPanelIsReadOnlyAndHasCopyControl(): void
    {
        $root = dirname(__DIR__, 2);
        $twig = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('id="ezs-debug-panel"', $twig);
        self::assertStringContainsString('id="ezs-debug-copy"', $twig);
        self::assertStringContainsString('app.request.port == 8790', $twig);
        self::assertSame(1, preg_match('/\bmethod\s*:\s*[\"\']GET[\"\']/', $js));
        self::assertSame(0, preg_match('/\bmethod\s*:\s*[\"\'](?:POST|PUT|PATCH|DELETE)[\"\']/i', $js));
        self::assertStringNotContainsString('JSON.stringify(data)', $js);
        self::assertStringContainsString('navigator.clipboard.writeText(report)', $js);
    }
}
