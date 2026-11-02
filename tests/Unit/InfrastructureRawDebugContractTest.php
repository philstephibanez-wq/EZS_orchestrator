<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureRawDebugContractTest extends TestCase
{
    public function testDiagnosticIsRawJsonConsoleWithoutSynthesizedTable(): void
    {
        $root = dirname(__DIR__, 2);
        $twig = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        $css = (string) file_get_contents($root.'/public/assets/ezs-debug-layout.css');

        self::assertStringContainsString('id="ezs-debug-output"', $twig);
        self::assertStringContainsString('id="ezs-debug-copy"', $twig);
        self::assertStringNotContainsString('id="ezs-debug-groups"', $twig);
        self::assertStringNotContainsString('id="ezs-debug-native"', $twig);
        self::assertStringContainsString('JSON.stringify(snapshot,null,2)', $js);
        self::assertStringContainsString('navigator.clipboard.writeText(value)', $js);
        self::assertStringContainsString('JSON.parse(raw)', $js);
        self::assertStringContainsString('redact(body)', $js);
        self::assertStringNotContainsString('safeStatus(', $js);
        self::assertStringNotContainsString('divergences', $js);
        self::assertStringContainsString('#000', $css);
        self::assertStringContainsString('#00ff66', $css);
    }
}
