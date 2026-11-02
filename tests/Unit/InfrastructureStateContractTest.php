<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureStateContractTest extends TestCase
{
    public function testHttpBadgeDoesNotClaimApplicationHealth(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($source);
        self::assertStringContainsString('function renderServiceBadge(group)', $source);
        self::assertStringContainsString('serviceNative[group]', $source);
        self::assertStringContainsString('serviceTransport[group]', $source);
        self::assertStringContainsString("'ONLINE'", $source);
        self::assertStringContainsString("'OFFLINE'", $source);
        self::assertStringContainsString("'ERREUR'", $source);
        self::assertStringNotContainsString("'HTTP accessible'", $source);
        self::assertStringNotContainsString("'Répond'", $source);
    }

    public function testFailedPermissionProbeRemainsFailClosedAndVisible(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($source);
        self::assertStringContainsString('function failGroup(group, reason)', $source);
        self::assertStringContainsString("failGroup(group,(xhr && xhr.status) || textStatus || 'réseau')", $source);
        self::assertStringContainsString("data-ezs-probe','unavailable'", $source);
        self::assertStringContainsString("data-ezs-probe','verified'", $source);
    }

    public function testAssetCacheIsVersioned(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/templates/infrastructure/index.html.twig');
        self::assertIsString($source);
        self::assertStringContainsString('ezs-infrastructure.js?v={{ orchestrator_version|url_encode }}', $source);
    }
}
