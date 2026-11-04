<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class InfrastructureHardOnlyR9DTest extends TestCase
{
    public function testInfrastructureNeverStartsReconciliationAndKeepsHardSupervision(): void
    {
        $root=dirname(__DIR__,2);
        $twig=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
        self::assertStringNotContainsString('ezs-rest-supervision.js', $twig);
        self::assertStringNotContainsString('ezs-recovery-preflight.js', $twig);
        self::assertStringNotContainsString('id="ezs-rest-supervision-state"', $twig);
        self::assertStringNotContainsString('id="ezs-web-recovery-preflight-status"', $twig);
        self::assertStringContainsString('ezs-web-hard.js', $twig);
        self::assertStringContainsString('ezs-prod-control.js', $twig);
        self::assertStringContainsString('ezs-dev-web-mode.js', $twig);
    }
    public function testDevProdCardsHaveMatchingPublicStatusAndMaintenanceMode(): void
    {
        $root=dirname(__DIR__,2);
        $twig=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
        foreach(['dev','prod'] as $site){
            foreach(['http-','tcp-','maintenance-button','normal-button','maintenance-badge','maintenance-banner'] as $key){
                self::assertStringContainsString('id="'.($key==='maintenance-button'||$key==='normal-button'||$key==='maintenance-badge'||$key==='maintenance-banner'?$site.'-'.$key:$key.$site).'"',$twig);
            }
        }
        $js=(string)file_get_contents($root.'/public/assets/ezs-dev-web-mode.js');
        self::assertStringContainsString('renderMode(mode)', $js);
        self::assertStringContainsString('renderMode(null)', $js);
        self::assertStringNotContainsString('Start-Process', $js);
        self::assertStringNotContainsString('Stop-Process', $js);
    }
}
