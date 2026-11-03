<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class EzsPlatformControlContractTest extends TestCase {
    public function testProtectedProdAndNativeLabTopology(): void {
        $root=dirname(__DIR__,2);
        $controller=file_get_contents($root.'/scripts/ezs_platform_control.ps1');
        $native=file_get_contents($root.'/scripts/ezs_native_site.ps1');
        self::assertIsString($controller);
        self::assertIsString($native);
        self::assertStringContainsString("[ValidateSet('prod','dev','lab','assistant')]",$controller);
        self::assertStringContainsString("if (\$Site -eq 'prod' -and \$Action -eq 'Stop')",$controller);
        self::assertStringContainsString('PROD_STOP_PROTECTED_REFUSED',$controller);
        self::assertStringContainsString('FRANKENPHP_ADAPT_FAILED',$controller);
        self::assertStringContainsString('ezs_assistant_stack.ps1',$controller);
        self::assertStringContainsString("[ValidateSet('prod','dev','lab')]",$native);
        self::assertStringContainsString('H:\EZStudio_lab\public\index.php',$native);
        self::assertStringContainsString('8702,8701',$native);
        self::assertStringContainsString('PROD_STOP_PROTECTED_REFUSED',$native);
        self::assertStringContainsString('NATIVE_CONFIG_LEGACY_FASTCGI_REFUSED',$native);
        self::assertStringNotContainsString('php-cgi.exe',$native);
        self::assertStringNotContainsString('Start-Process -FilePath $qwenExe',$controller);
    }
}
