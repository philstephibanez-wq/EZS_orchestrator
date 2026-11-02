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
        self::assertStringContainsString("'En ligne'", $source);
        self::assertStringContainsString("'En erreur'", $source);
        self::assertStringNotContainsString("'HTTP accessible'", $source);
        self::assertStringNotContainsString("'Répond'", $source);
    }

    public function testFailedPermissionProbeRemainsFailClosedAndVisible(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($source);
        self::assertStringContainsString('function disableAll()', $source);
        self::assertStringContainsString('indicateUnavailable(', $source);
        self::assertStringContainsString("data-ezs-probe', 'unavailable'", $source);
        self::assertStringContainsString("data-ezs-probe', 'verified'", $source);
    }

    public function testAssetCacheIsVersioned(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/templates/infrastructure/index.html.twig');
        self::assertIsString($source);
        self::assertStringContainsString('ezs-infrastructure.js?v={{ orchestrator_version|url_encode }}', $source);
    }
}
