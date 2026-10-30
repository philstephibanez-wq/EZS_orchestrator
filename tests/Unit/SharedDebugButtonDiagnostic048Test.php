<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugButtonDiagnostic048Test extends TestCase
{
    public function testReadOnlyButtonMismatchAndTransitionDiagnostics(): void
    {
        $root = dirname(__DIR__, 2);
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('MutationObserver', $script);
        self::assertStringContainsString("attributeFilter:['disabled']", $script);
        self::assertStringContainsString('ÉCARTS API / DOM', $script);
        self::assertStringContainsString('CHANGEMENTS DES BOUTONS OBSERVÉS', $script);
        self::assertStringContainsString('d.stop !== String(item?.stop !== true)', $script);
        self::assertStringContainsString("state === 'RUNNING' && item?.restart === true", $script);
        self::assertStringContainsString("state === 'STOPPED' && item?.start === true", $script);
        self::assertStringContainsString('d.label === expectedMode && d.start !== String(expectedDisabled)', $script);
        self::assertSame(2, substr_count($script, "get('/api/v2/infrastructure/"));
        self::assertSame(0, preg_match('/\bmethod\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\']/i', $script));
    }
}
