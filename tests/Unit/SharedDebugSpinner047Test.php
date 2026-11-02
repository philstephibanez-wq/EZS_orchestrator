<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SharedDebugSpinner047Test extends TestCase
{
    public function testSpinnerFollowsReadOnlyCollection(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('id="ezs-debug-spinner"', $layout);
        self::assertStringContainsString('spinner-border-sm', $layout);
        self::assertStringContainsString('role="status"', $layout);
        self::assertStringContainsString('aria-label="Collecte du diagnostic en cours"', $layout);
        self::assertStringContainsString("spinner.classList.remove('d-none')", $script);
        self::assertStringContainsString("spinner.classList.add('d-none')", $script);
        $start = strpos($script, "spinner.classList.remove('d-none')");
        $end = strpos($script, "spinner.classList.add('d-none')", $start);
        self::assertIsInt($start);
        self::assertIsInt($end);
        self::assertGreaterThan($start, $end);
        self::assertStringContainsString('for (const url of sources)', $script);
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $script);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $script);
        self::assertStringContainsString("request:{method:'POST'", $script);
        self::assertStringContainsString("method:'GET'", $script);
        self::assertStringNotContainsString("fetch(url, {method:'POST'", $script);
    }
}
