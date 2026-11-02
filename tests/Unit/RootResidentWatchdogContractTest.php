<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentWatchdogContractTest extends TestCase
{
    public function testResidentOnlyInvokesDevTick(): void
    {
        $root = dirname(__DIR__, 2);
        $resident = file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $tick = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($resident);
        self::assertIsString($tick);
        self::assertStringContainsString('& $tick -DevOnly', $resident);
        self::assertStringContainsString('EZS_ROOT_DEV_RESIDENT_SINGLETON', $resident);
        self::assertStringContainsString("[switch]"."DevOnly", str_replace("$"."DevOnly", "DevOnly", $tick));
        self::assertStringContainsString("if (DevOnly)", str_replace("$"."DevOnly", "DevOnly", $tick));
        self::assertStringContainsString('Where-Object { $_.Name -eq', $tick);
    }
}
