<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeAdaptStderrR5BContractTest extends TestCase
{
    public function testNativeAdaptWarningsAreNonFatalButNonzeroExitRefused(): void
    {
        $script = (string) file_get_contents(dirname(__DIR__, 2).'/scripts/ezs_platform_control.ps1');
        self::assertStringContainsString("$".'previousErrorActionPreference=$ErrorActionPreference', $script);
        self::assertStringContainsString("$"."ErrorActionPreference='Continue'", $script);
        self::assertStringContainsString('$null=& $exe adapt --config $config --adapter caddyfile 2>&1', $script);
        self::assertStringContainsString('$adaptExitCode=$LASTEXITCODE', $script);
        self::assertStringContainsString('} finally {', $script);
        self::assertStringContainsString('$ErrorActionPreference=$previousErrorActionPreference', $script);
        self::assertStringContainsString('if($adaptExitCode -ne 0)', $script);
        self::assertStringContainsString('FRANKENPHP_ADAPT_FAILED', $script);
        self::assertStringContainsString('CADDY_CONFIG_FASTCGI_REFUSED', $script);
        self::assertStringContainsString('PROD_STOP_PROTECTED_REFUSED', $script);
        self::assertStringNotContainsString('fmt --overwrite', $script);
        self::assertStringNotContainsString('Start-Process', $script);
    }
}
