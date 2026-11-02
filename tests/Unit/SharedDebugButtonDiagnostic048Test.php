<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SharedDebugButtonDiagnostic048Test extends TestCase
{
    public function testRawDomButtonSnapshotWithoutBusinessInterpretation(): void
    {
        $root = dirname(__DIR__, 2);
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('function domDump()', $script);
        self::assertStringContainsString('card_present: Boolean(card)', $script);
        self::assertStringContainsString('disabled:b.disabled', $script);
        self::assertStringContainsString("b.getAttribute('aria-label')", $script);
        self::assertStringContainsString('timestamp_utc:new Date().toISOString()', $script);
        self::assertStringNotContainsString('ÉCARTS API / DOM', $script);
        self::assertStringNotContainsString('expectedMode', $script);
        self::assertSame(4, substr_count($script, "'/api/v2/infrastructure/"));
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $script);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $script);
        self::assertStringContainsString("request:{method:'POST'", $script);
        self::assertStringContainsString("method:'GET'", $script);
        self::assertStringNotContainsString("fetch(url, {method:'POST'", $script);
    }
}
