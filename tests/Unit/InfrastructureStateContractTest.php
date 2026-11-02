<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureStateContractTest extends TestCase
{
    public function testHttpBadgeDoesNotClaimApplicationHealth(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($source);
        self::assertStringContainsString("'HTTP accessible'", $source);
        self::assertStringContainsString("'HTTP en erreur'", $source);
        self::assertStringContainsString("'HTTP ' + item.http_status + ' · redirection'", $source);
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
