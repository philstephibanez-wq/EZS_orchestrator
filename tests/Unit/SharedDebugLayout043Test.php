<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SharedDebugLayout043Test extends TestCase
{
    public function testSharedDevPanelIsReadOnlyAndCopiesDisplayedJson(): void
    {
        $root = dirname(__DIR__, 2);
        $twig = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('id="ezs-debug-panel"', $twig);
        self::assertStringContainsString('id="ezs-debug-copy"', $twig);
        self::assertStringContainsString('id="ezs-debug-output"', $twig);
        self::assertStringContainsString('app.request.port == 8790', $twig);
        self::assertSame(1, preg_match('/\bmethod\s*:\s*["\']GET["\']/', $js));
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $js);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $js);
        self::assertStringContainsString("request:{method:'POST'", $js);
        self::assertStringContainsString("method:'GET'", $js);
        self::assertStringNotContainsString("fetch(url, {method:'POST'", $js);
        self::assertStringContainsString('navigator.clipboard.writeText(value)', $js);
        self::assertStringContainsString('const value = output.textContent', $js);
    }
}
