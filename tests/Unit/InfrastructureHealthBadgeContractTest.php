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
        self::assertStringContainsString("'En ligne'", $js);
        self::assertStringContainsString("'En erreur'", $js);
        self::assertStringContainsString('\\u00c0 v\\u00e9rifier', $js);
        self::assertStringContainsString('serviceNative[group] = null; renderServiceBadge(group);', $js);
        self::assertStringContainsString('serviceTransport[group] = null;', $js);
        self::assertStringNotContainsString("'HTTP accessible'", $js);
    }
}
