<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\Controller\WebHardPingController;
final class WebHardPingR8Test extends TestCase {
    public function testPortTopologyAndLoopbackGate():void {
        $sites=WebHardPingController::definitions();
        self::assertSame([8502,8602],$sites['dev']['ports']);
        self::assertSame([8702,8701],$sites['lab']['ports']);
        self::assertSame([8712,8713],$sites['assistant']['ports']);
        self::assertSame([8501,8510,8511],$sites['prod']['ports']);
        self::assertTrue(WebHardPingController::allowed('dev','localhost','::1'));
        self::assertFalse(WebHardPingController::allowed('prod','localhost','::1'));
    }
    public function testHardSuccessRequiresPortsAndHttp():void {
        self::assertSame('OK',WebHardPingController::classify(['8502'=>true,'8602'=>true],['status'=>302],false));
        self::assertSame('ECHEC',WebHardPingController::classify(['8502'=>true,'8602'=>false],['status'=>200],false));
        self::assertSame('ECHEC',WebHardPingController::classify(['8502'=>true,'8602'=>true],['status'=>null],false));
        self::assertSame('MAINTENANCE',WebHardPingController::classify(['8501'=>true,'8510'=>false,'8511'=>false],['status'=>503],true));
    }
    public function testReadOnlySourceAndDump():void {
        $root=dirname(__DIR__,2);
        $js=file_get_contents($root.'/public/assets/ezs-web-hard.js');
        $dump=file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('/api/v2/infrastructure/web-hard-ping',$js);
        self::assertStringContainsString('/api/v2/infrastructure/web-hard-ping',$dump);
        self::assertStringNotContainsString('Start-Process',$js);
        self::assertStringNotContainsString('Stop-Process',$js);
    }
}
