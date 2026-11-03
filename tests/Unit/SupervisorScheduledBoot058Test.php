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
            self::assertSame(['dev'], ServiceSupervisorCommand::planned($reloaded->all()));
            $state->set('dev', DesiredServiceState::STOPPED);
            self::assertSame([], ServiceSupervisorCommand::planned((new DesiredServiceState($path))->all()));
        } finally {
            @unlink($dir.'/state.json');
            @unlink($dir.'/desired-services.lock');
            @rmdir($dir);
        }
    }

    public function testWindowsTaskMustBeOptInAndUseExistingTick(): void
    {
        $root=dirname(__DIR__,2);
        $legacy=file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        $legacyTask=file_get_contents($root.'/scripts/ezs_supervisor_task.ps1');
        $task=file_get_contents($root.'/scripts/ezs_root_resident_task.ps1');
        $resident=file_get_contents($root.'/scripts/ezs_supervisor_resident.ps1');
        $hidden=file_get_contents($root.'/scripts/ezs_supervisor_resident_hidden.vbs');
        foreach ([$legacy,$legacyTask,$task,$resident,$hidden] as $source) self::assertIsString($source);
        self::assertStringContainsString("throw 'EZS_LEGACY_SUPERVISOR_REMOVED_USE_NATIVE_FRANKENPHP'",$legacy);
        self::assertStringNotContainsString('Start-RootFastCgi',$legacy);
        self::assertStringNotContainsString('Start-Process',$legacy);
        self::assertStringContainsString("'InstallDisabled'",$task);
        self::assertStringContainsString('EZS_ROOT_TASK_ALREADY_EXISTS',$task);
        self::assertStringContainsString('EZS_LEGACY_TASK_PRESENT_REFUSED',$task);
        self::assertStringContainsString('New-ScheduledTaskSettingsSet',$task);
        self::assertStringContainsString('-Disable',$task);
        self::assertStringContainsString('ezs_root_frankenphp_watchdog.ps1',$resident);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$resident);
        self::assertStringContainsString('WshShell.Run',$hidden);
        self::assertStringContainsString(', 0, True',$hidden);
        // The historical task installer is not the canonical ROOT entrypoint.
        self::assertStringContainsString('ezs_supervisor_tick.ps1',$legacyTask);
    }
}
