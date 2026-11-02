<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootResidentTaskVariableContractTest extends TestCase
{
    public function testTaskActionDoesNotOverwriteValidatedParameter(): void
    {
        $root = dirname(__DIR__, 2);
        $task = file_get_contents($root.'/scripts/ezs_root_resident_task.ps1');
        self::assertIsString($task);
        self::assertStringContainsString("[string]$".'Action', $task);
        self::assertStringContainsString('$taskExecAction = New-ScheduledTaskAction', $task);
        self::assertStringContainsString('-Action $taskExecAction -Trigger', $task);
        self::assertDoesNotMatchRegularExpression('/\$action\s*=\s*New-ScheduledTaskAction/i', $task);
        self::assertStringContainsString("'4.2d35'", $task);
        self::assertStringContainsString("$".'legacy', $task);
        self::assertStringContainsString("-Disable", $task);
    }
}
