<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class InfrastructureRawActionTraceContractTest extends TestCase
{
    public function testActionTransportIsObservedButNeverDispatched(): void
    {
        $root = dirname(__DIR__, 2);
        $js = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('ezsActionTrace', $js);
        self::assertStringContainsString('.ajaxSend(function', $js);
        self::assertStringContainsString('.ajaxComplete(function', $js);
        self::assertStringContainsString('ezsActionStarted.get(xhr)', $js);
        self::assertStringContainsString('response.body = redact(xhr.responseJSON)', $js);
        self::assertStringContainsString('action_requests_and_responses:ezsActionTrace.slice()', $js);
        self::assertStringContainsString('output.textContent = JSON.stringify(current,null,2)', $js);
        self::assertStringNotContainsString('.ajax({', $js);
        self::assertStringNotContainsString("fetch('/api/v2/infrastructure/dev-groups/", $js);
        self::assertStringNotContainsString('settings.headers', $js);
    }
}
