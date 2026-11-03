<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class NativeLabAssistantTopologyContractTest extends TestCase
{
    public function testSeparateNativeSitesPreserveExistingProdAndDevContracts(): void
    {
        $root=dirname(__DIR__,2).'/config/frankenphp/';
        $lab=file_get_contents($root.'Caddyfile.lab.native');
        $assistant=file_get_contents($root.'Caddyfile.assistant.native');
        $dev=file_get_contents($root.'Caddyfile.dev.native');
        $prod=file_get_contents($root.'Caddyfile.prod.native');
        foreach ([$lab,$assistant,$dev,$prod] as $config) {
            self::assertIsString($config);
            self::assertStringContainsString('php_server', $config);
            self::assertStringNotContainsString('php_fastcgi', $config);
            self::assertStringNotContainsString('php-cgi', $config);
        }
        self::assertStringContainsString('127.0.0.1:8702', $lab);
        self::assertStringContainsString('127.0.0.1:8701', $lab);
        self::assertStringContainsString('H:/EZStudio_lab/public', $lab);
        self::assertStringContainsString('127.0.0.1:8712', $assistant);
        self::assertStringContainsString('127.0.0.1:8713', $assistant);
        self::assertStringContainsString('H:/EZStudioLab_assistant/public', $assistant);
        self::assertStringNotContainsString('8720', $assistant);
        self::assertStringContainsString('127.0.0.1:8502', $dev);
        self::assertStringContainsString('127.0.0.1:8602', $dev);
        self::assertStringContainsString('/internal/media/auth', $dev);
        self::assertStringContainsString('127.0.0.1:8501', $prod);
        self::assertStringContainsString('127.0.0.1:8510', $prod);
        self::assertStringContainsString('127.0.0.1:8511', $prod);
        self::assertStringContainsString('X-Forwarded-Proto https', $prod);
        self::assertStringContainsString('X-Forwarded-Host {http.request.host}', $prod);
        self::assertStringContainsString('/internal/media/auth', $prod);
    }
    public function testAssistantStartStopStillOwnLlama(): void
    {
        $root=dirname(__DIR__,2);
        $bridge=file_get_contents($root.'/scripts/ezs_assistant_stack.ps1');
        self::assertIsString($bridge);
        self::assertStringContainsString('scripts\\start.ps1', $bridge);
        self::assertStringContainsString('scripts\\stop.ps1', $bridge);
        self::assertStringNotContainsString('Start-Process -FilePath $qwenExe', $bridge);
        self::assertStringNotContainsString('Stop-Process -Id $p.ProcessId', $bridge);
    }
}
