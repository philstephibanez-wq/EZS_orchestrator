<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class EzscoreCardLayout4_3A0Test extends TestCase
{
    public function testProdMaintenanceBannerIsInsideHeaderAndOnlyOnce(): void
    {
        $source = (string) file_get_contents(dirname(__DIR__, 2).'/templates/infrastructure/index.html.twig');
        $prod = strpos($source, 'id="ezs-prod-card"');
        $headerEnd = strpos($source, '<div class="card-body">', $prod);
        $banner = strpos($source, 'id="prod-maintenance-banner"', $prod);
        self::assertNotFalse($prod);
        self::assertNotFalse($headerEnd);
        self::assertNotFalse($banner);
        self::assertLessThan($headerEnd, $banner, 'Bandeau dans la barre de titre PROD');
        self::assertSame(1, substr_count($source, 'id="prod-maintenance-banner"'));
        self::assertSame(1, substr_count($source, 'id="prod-maintenance-badge"'));
        self::assertSame(1, substr_count($source, 'id="prod-control-status"'));
    }

    public function testOperationalControlsAndCollapsedTechnicalDetailsStayPresent(): void
    {
        $source = (string) file_get_contents(dirname(__DIR__, 2).'/templates/infrastructure/index.html.twig');
        foreach (['dev-mode-card','ezs-prod-card','dev-maintenance-button','prod-maintenance-button',
            'dev-normal-button','prod-normal-button','soft-dev','soft-prod'] as $id) {
            self::assertStringContainsString('id="'.$id.'"', $source);
        }
        $css = (string) file_get_contents(dirname(__DIR__, 2).'/public/assets/ezs-ezscore-cards.css');
        self::assertStringContainsString('#ezs-prod-card #prod-maintenance-banner', $css);
        self::assertStringContainsString('#ezs-prod-card #prod-maintenance-badge { display: none !important; }', $css);
        self::assertStringContainsString('ezs-ezscore-cards.css?v={{ orchestrator_version|url_encode }}', $source);
    }
}
