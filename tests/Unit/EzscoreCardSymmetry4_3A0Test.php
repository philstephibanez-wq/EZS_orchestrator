<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class EzscoreCardSymmetry4_3A0Test extends TestCase
{
    public function testMaintenanceBannersAreUniqueAndPlacedInBothHeaders(): void
    {
        $source = (string) file_get_contents(dirname(__DIR__, 2).'/templates/infrastructure/index.html.twig');
        foreach ([
            ['card' => 'dev-mode-card', 'banner' => 'dev-maintenance-banner', 'status' => 'state-dev', 'legacy' => 'dev-maintenance-badge'],
            ['card' => 'ezs-prod-card', 'banner' => 'prod-maintenance-banner', 'status' => 'prod-control-status', 'legacy' => 'prod-maintenance-badge'],
        ] as $card) {
            foreach (['card', 'banner', 'status', 'legacy'] as $element) {
                self::assertSame(1, substr_count($source, 'id="'.$card[$element].'"'), $card[$element]);
            }
            $start = strpos($source, 'id="'.$card['card'].'"');
            self::assertNotFalse($start);
            $nextBody = strpos($source, '<div class="card-body">', $start);
            self::assertNotFalse($nextBody);
            $banner = strpos($source, 'id="'.$card['banner'].'"', $start);
            self::assertNotFalse($banner);
            self::assertLessThan($nextBody, $banner, $card['banner'].' doit rester dans en-tete');
        }
    }

    public function testDevAndProdUseSameResponsiveHeaderRulesAndPreserveControls(): void
    {
        $root = dirname(__DIR__, 2);
        $css = (string) file_get_contents($root.'/public/assets/ezs-ezscore-cards.css');
        $twig = (string) file_get_contents($root.'/templates/infrastructure/index.html.twig');
        foreach (['dev', 'prod'] as $mode) {
            $card = $mode === 'dev' ? '#dev-mode-card' : '#ezs-prod-card';
            $banner = $mode.'-maintenance-banner';
            $legacy = $mode.'-maintenance-badge';
            self::assertStringContainsString($card.' #'.$banner, $css);
            self::assertStringContainsString($card.' #'.$legacy.' { display: none !important; }', $css);
            self::assertStringContainsString('id="'.$mode.'-maintenance-button"', $twig);
            self::assertStringContainsString('id="'.$mode.'-normal-button"', $twig);
        }
        self::assertStringContainsString('#dev-mode-card #dev-maintenance-banner { order: 3; flex-basis: 100%; }', $css);
        self::assertStringContainsString('#ezs-prod-card #prod-maintenance-banner { order: 3; flex-basis: 100%; }', $css);
        self::assertStringContainsString('id="soft-dev"', $twig);
        self::assertStringContainsString('id="soft-prod"', $twig);
    }
}
