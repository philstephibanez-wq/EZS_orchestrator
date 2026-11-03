<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentTaskVariableContractTest extends TestCase {
    public function testTaskUsesFrankenphpVersionAndCorrectScheduledTaskAction(): void {
        $task=file_get_contents(dirname(__DIR__,2).'/scripts/ezs_root_resident_task.ps1');
        self::assertStringContainsString('[string]$Action',$task);
        self::assertStringContainsString('$taskExecAction=New-ScheduledTaskAction',$task);
        self::assertStringContainsString('-Action $taskExecAction -Trigger',$task);
        self::assertStringContainsString("'4.2d38'",$task);
        self::assertStringContainsString('EZS_LEGACY_TASK_PRESENT_REFUSED',$task);
        self::assertStringContainsString('-Disable',$task);
    }
}
