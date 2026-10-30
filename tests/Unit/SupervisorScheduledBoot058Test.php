<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\DesiredServiceState;
use Ezs\Web\Module\Infrastructure\ServiceSupervisorCommand;
use PHPUnit\Framework\TestCase;

final class SupervisorScheduledBoot058Test extends TestCase
{
    public function testColdBootDefaultsToNoAutomaticStart(): void
    {
        $path = sys_get_temp_dir().'/ezs-boot-'.bin2hex(random_bytes(6)).'.json';
        $state = new DesiredServiceState($path);
        self::assertSame([], ServiceSupervisorCommand::planned($state->all()));
        self::assertSame(DesiredServiceState::STOPPED, $state->get('prod'));
        self::assertSame(DesiredServiceState::STOPPED, $state->get('root'));
    }

    public function testPersistedIntentIsAppliedInDependencyOrderOnlyForRunningGroups(): void
    {
        $dir = sys_get_temp_dir().'/ezs-boot-'.bin2hex(random_bytes(6));
        mkdir($dir);
        try {
            $path = $dir.'/state.json';
            $state = new DesiredServiceState($path);
            $state->setMany(['root' => DesiredServiceState::RUNNING, 'dev' => DesiredServiceState::RUNNING,
                'prod' => DesiredServiceState::STOPPED]);
            $reloaded = new DesiredServiceState($path);
            self::assertSame(['root','dev'], ServiceSupervisorCommand::planned($reloaded->all()));
            $state->set('dev', DesiredServiceState::STOPPED);
            self::assertSame(['root'], ServiceSupervisorCommand::planned((new DesiredServiceState($path))->all()));
        } finally {
            @unlink($dir.'/state.json');
            @unlink($dir.'/desired-services.lock');
            @rmdir($dir);
        }
    }

    public function testWindowsTaskMustBeOptInAndUseExistingTick(): void
    {
        $root = dirname(__DIR__, 2);
        $installer = file_get_contents($root.'/scripts/ezs_supervisor_task.ps1');
        $runner = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($installer);
        self::assertIsString($runner);
        self::assertStringContainsString("'Install','Update','Remove'", $installer);
        self::assertStringContainsString('EZS_SUPERVISOR_TASK_ALREADY_EXISTS', $installer);
        self::assertStringContainsString('ezs:services tick', $runner);
        self::assertStringNotContainsString('ezs:services start', $runner);
        self::assertStringNotContainsString('extension=$extension', $runner);
        self::assertStringContainsString('wscript.exe', $installer);
        self::assertStringContainsString('Set-ScheduledTask', $installer);
        self::assertStringContainsString('EZS_SUPERVISOR_TASK_UPDATED_HIDDEN', $installer);
        $hidden = file_get_contents($root.'/scripts/ezs_supervisor_hidden.vbs');
        self::assertIsString($hidden);
        self::assertStringContainsString('WshShell.Run', $hidden);
        self::assertStringContainsString(', 0, True', $hidden);
    }
}
