<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureProdStatusContractTest extends TestCase
{
    public function testProdStatusUsesCommonServiceLabels(): void
    {
        $js = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-prod-control.js');
        self::assertIsString($js);
        self::assertStringContainsString("setStatus('En ligne','success')", $js);
        self::assertStringContainsString("setStatus('En erreur','danger')", $js);
        self::assertStringContainsString("setStatus('À vérifier','warning')", $js);
        self::assertStringNotContainsString("setStatus('Répond'", $js);
        self::assertStringContainsString('showMaintenance(typeof d.maintenance', $js);
        self::assertStringContainsString('capabilities={maintenance:false,normal:false};setButtons();', $js);
    }

    public function testProdAssetCacheIsVersioned(): void
    {
        $twig = file_get_contents(dirname(__DIR__, 2) . '/templates/infrastructure/index.html.twig');
        self::assertIsString($twig);
        self::assertStringContainsString('ezs-prod-control.js?v={{ orchestrator_version|url_encode }}', $twig);
    }
}
