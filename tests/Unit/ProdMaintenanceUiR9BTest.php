<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class ProdMaintenanceUiR9BTest extends TestCase
{
    public function testProdMaintenanceBadgeIsNotAnOutageAndWebHardShowsHttpAndTcp(): void
    {
        $root=dirname(__DIR__,2);
        $prod=(string)file_get_contents($root.'/public/assets/ezs-prod-control.js');
        $hard=(string)file_get_contents($root.'/public/assets/ezs-web-hard.js');
        $twig=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
        self::assertStringContainsString("d.maintenance===true && d.caddy_listening",$prod);
        self::assertStringContainsString("setStatus('Maintenance','warning')",$prod);
        self::assertStringContainsString("$('#http-prod')",$hard);
        self::assertStringContainsString("$('#tcp-prod')",$hard);
        self::assertStringContainsString('id="http-prod"',$twig);
        self::assertStringContainsString('id="tcp-prod"',$twig);
        self::assertStringContainsString('id="dev-maintenance-button"',$twig);
        self::assertStringContainsString('id="prod-maintenance-button"',$twig);
    }
}
