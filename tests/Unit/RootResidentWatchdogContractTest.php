<?php

declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentWatchdogContractTest extends TestCase
{
    public function testRootObserverIsPassiveAndResidentNeverBootsSites(): void
    {
        $root=dirname(__DIR__,2);
        $resident=(string)file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $watchdog=(string)file_get_contents($root.'/scripts/ezs_root_frankenphp_watchdog.ps1');
        self::assertStringContainsString('ezs_root_frankenphp_watchdog.ps1',$resident);
        self::assertStringContainsString('& $watchdog -Once',$resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON',$resident);
        self::assertStringContainsString('ROOT_WEB_UNAVAILABLE',$watchdog);
        self::assertStringContainsString('127.0.0.1:8790/',$watchdog);
        foreach(['Stop-Process','Start-Process','Start-Service','Stop-Service','Get-CimInstance'] as $command){
            self::assertStringNotContainsString($command,$watchdog);
        }
        self::assertStringNotContainsString('-Action Boot',$resident);
    }
}
