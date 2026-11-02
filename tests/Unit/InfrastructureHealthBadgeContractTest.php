<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureHealthBadgeContractTest extends TestCase
{
    public function testUnifiedBadgeUsesHttpAndNativeState(): void
    {
        $js = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($js);
        self::assertStringContainsString('function renderServiceBadge(group)', $js);
        self::assertStringContainsString("native === 'STOPPED'", $js);
        self::assertStringContainsString("native === 'RUNNING'", $js);
        self::assertStringContainsString('http >= 200 && http < 400', $js);
        self::assertStringContainsString("'ONLINE'", $js);
        self::assertStringContainsString("'ERREUR'", $js);
        self::assertStringContainsString("'OFFLINE'", $js);
        self::assertStringContainsString('serviceNative[group] = null;', $js);
        self::assertStringContainsString('serviceDesired[group] = null;', $js);
        self::assertStringContainsString('renderServiceBadge(group);', $js);
        self::assertStringContainsString('serviceTransport[group] = null;', $js);
        self::assertStringNotContainsString("'HTTP accessible'", $js);
    }
}
