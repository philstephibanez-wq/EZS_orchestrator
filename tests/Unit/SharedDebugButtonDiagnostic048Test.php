<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SharedDebugButtonDiagnostic048Test extends TestCase
{
    public function testRawDomAndWebHardPingSource(): void
    {
        $root=dirname(__DIR__,2);
        $script=(string)file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('function domDump()',$script);
        self::assertStringContainsString('card_present: Boolean(card)',$script);
        self::assertStringContainsString('timestamp_utc:new Date().toISOString()',$script);
        self::assertSame(1,substr_count($script,"'/api/v2/infrastructure/"));
        self::assertStringContainsString("'/api/v2/infrastructure/web-hard-ping'",$script);
        self::assertStringContainsString("method:'GET'",$script);
        self::assertStringNotContainsString("fetch(url, {method:'POST'",$script);
        self::assertStringContainsString('action_requests_and_responses:ezsActionTrace.slice()',$script);
    }
}
