<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class UnifiedDebug045Test extends TestCase
{
    public function testSingleSharedRawJsonDiagnosticWithWebHardPing(): void
    {
        $root=dirname(__DIR__,2);
        $layout=(string)file_get_contents($root.'/templates/layout/base.html.twig');
        $js=(string)file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        $controller=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/WebHardPingController.php');
        self::assertStringContainsString('id="ezs-debug-output"',$layout);
        self::assertStringContainsString('Copier le diagnostic complet',$layout);
        self::assertStringContainsString('/api/v2/infrastructure/web-hard-ping',$js);
        self::assertStringContainsString('JSON.stringify(snapshot,null,2)',$js);
        self::assertStringContainsString('navigator.clipboard.writeText(value)',$js);
        self::assertStringContainsString("methods:['GET']",$controller);
        self::assertStringContainsString('stream_socket_client',$controller);
        self::assertStringNotContainsString('Start-Process',$controller);
        self::assertStringNotContainsString('Stop-Process',$controller);
    }
}
