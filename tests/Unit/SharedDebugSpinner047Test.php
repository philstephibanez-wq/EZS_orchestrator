<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugSpinner047Test extends TestCase
{
    public function testSpinnerFollowsDiagnosticCollectionWithoutExtraRequests(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');

        self::assertStringContainsString('id="ezs-debug-spinner"', $layout);
        self::assertStringContainsString('spinner-border-sm', $layout);
        self::assertStringContainsString('d-none', $layout);
        self::assertStringContainsString('role="status"', $layout);
        self::assertStringContainsString('aria-label="Collecte du diagnostic en cours"', $layout);
        self::assertStringContainsString("const spinner = document.getElementById('ezs-debug-spinner')", $script);
        self::assertStringContainsString("spinner.classList.remove('d-none')", $script);
        self::assertStringContainsString("spinner.classList.add('d-none')", $script);
        self::assertLessThan(strpos($script, "status.textContent = report ?"), strpos($script, "spinner.classList.remove('d-none')"));
        self::assertLessThan(strpos($script, "busy = false;", strpos($script, 'async function collect()')), strpos($script, "spinner.classList.add('d-none')"));
        self::assertSame(2, substr_count($script, "get('/api/v2/infrastructure/"));
        self::assertSame(0, preg_match('/\bmethod\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\']/i', $script));
    }
}
