<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class NativeProdDevConfigContractTest extends TestCase {
    public function testNoFastCgiInNativeSiteConfigs(): void {
        $root=dirname(__DIR__,2);
        foreach(['prod'=>[8501,8510,8511],'dev'=>[8502,8602]] as $site=>$ports){
            $content=file_get_contents($root.'/config/frankenphp/Caddyfile.'.$site.'.native');
            self::assertIsString($content);
            self::assertStringNotContainsString('php_fastcgi',$content);
            foreach($ports as $port){self::assertStringContainsString('127.0.0.1:'.$port,$content);}
            self::assertStringContainsString('php_server',$content);
        }
        $launcher=(string)file_get_contents($root.'/scripts/ezs_native_site.ps1');
        self::assertStringNotContainsString('Start-Process -FilePath $phpCgi',$launcher);
        self::assertStringContainsString('NATIVE_CONFIG_LEGACY_FASTCGI_REFUSED',$launcher);
        self::assertStringNotContainsString('desired-services.json',$launcher);
        self::assertStringContainsString('PROCESS_IDENTITY_REATTEST_FAILED',$launcher);
        self::assertStringContainsString('PROD_STOP_PROTECTED_REFUSED',$launcher);
    }
}
