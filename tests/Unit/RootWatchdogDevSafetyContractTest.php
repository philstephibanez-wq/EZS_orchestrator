<?php

declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootWatchdogDevSafetyContractTest extends TestCase
{
    public function testNoRecoveryCanMutateSharedFrankenphp(): void
    {
        $root=dirname(__DIR__,2);
        $legacy=(string)file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $watchdog=(string)file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        $resident=(string)file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringContainsString('EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP',$legacy);
        foreach(['Stop-Process','Start-Process','Start-Service','Stop-Service'] as $mutation){
            self::assertStringNotContainsString($mutation,$watchdog);
            self::assertStringNotContainsString($mutation,$resident);
        }
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
        self::assertStringContainsString('ROOT_WEB_UNAVAILABLE',$watchdog);
    }
}
