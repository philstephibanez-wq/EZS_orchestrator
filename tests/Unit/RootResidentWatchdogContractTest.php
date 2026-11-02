<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentWatchdogContractTest extends TestCase
{
    public function testResidentInvokesRootOnlyTick(): void
    {
        $root = dirname(__DIR__, 2);
        $resident = file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $tick = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($resident);
        self::assertIsString($tick);
        self::assertStringContainsString('& $tick -RootOnly', $resident);
        self::assertStringNotContainsString('& $tick -DevOnly', $resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON', $resident);
        self::assertStringContainsString('[switch]$RootOnly', $tick);
        self::assertStringContainsString('if ($RootOnly) { $specs = @() }', $tick);
        self::assertStringContainsString('if ($DevOnly)', $tick);
    }
}
