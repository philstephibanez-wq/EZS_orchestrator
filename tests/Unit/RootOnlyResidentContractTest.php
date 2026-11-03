<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootOnlyResidentContractTest extends TestCase {
    public function testExclusiveRootTask(): void {
        $root=dirname(__DIR__,2);
        $resident=file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $task=file_get_contents($root.'/scripts/ezs_root_resident_task.ps1');
        self::assertStringContainsString('ezs_root_frankenphp_watchdog.ps1',$resident);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
        self::assertStringContainsString('EZS_ROOT_RESIDENT_SINGLETON',$resident);
        self::assertStringContainsString("EZS_ROOT_resident",$task);
        self::assertStringContainsString('EZS_ROOT_resident',$task);
        self::assertStringContainsString('EZS_orchestrator_supervisor',$task);
        self::assertStringContainsString('EZS_LEGACY_TASK_PRESENT_REFUSED',$task);
        self::assertStringNotContainsString('Set-ScheduledTask -TaskName $legacy',$task);
    }
}
