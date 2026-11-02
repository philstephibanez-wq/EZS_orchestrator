<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootOnlyResidentContractTest extends TestCase
{
    public function testIsolationAndSeparateTask(): void
    {
        $root = dirname(__DIR__, 2);
        $tick = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $resident = file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $task = file_get_contents($root.'/scripts/ezs_root_resident_task.ps1');
        self::assertIsString($tick);
        self::assertIsString($resident);
        self::assertIsString($task);
        self::assertStringContainsString('[switch]$RootOnly', $tick);
        self::assertStringContainsString('if ($RootOnly) { $specs = @() }', $tick);
        self::assertStringContainsString('& $tick -RootOnly', $resident);
        self::assertStringNotContainsString('& $tick -DevOnly', $resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON', $resident);
        self::assertStringContainsString("\$name = 'EZS_ROOT_resident'", $task);
        self::assertStringContainsString("\$legacy = 'EZS_orchestrator_supervisor'", $task);
        self::assertStringContainsString("-Disable", $task);
        self::assertStringNotContainsString('Set-ScheduledTask -TaskName $legacy', $task);
        self::assertStringNotContainsString('Disable-ScheduledTask -TaskName $legacy', $task);
        self::assertStringNotContainsString('Stop-ScheduledTask -TaskName $legacy', $task);
    }
}
