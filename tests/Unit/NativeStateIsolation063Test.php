<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\DesiredServiceState;

final class NativeStateIsolation063Test extends TestCase
{
    public function testMissingStateDefaultsToStoppedWithoutTouchingLiveState(): void
    {
        $directory = sys_get_temp_dir().'/ezs-state-063-'.bin2hex(random_bytes(8));
        self::assertTrue(mkdir($directory));
        $path = $directory.'/desired.json';
        try {
            $state = new DesiredServiceState($path);
            $values = $state->all();
            self::assertSame(['root','dev','lab','assistant','assistant_ai','prod'], array_keys($values));
            foreach ($values as $value) self::assertSame(DesiredServiceState::STOPPED,$value);
            self::assertFileDoesNotExist($path);
        } finally {
            foreach (glob($directory.'/*') ?: [] as $file) if (is_file($file)) unlink($file);
            rmdir($directory);
        }
    }

    public function testStoppedIntentSurvivesFreshInstance(): void
    {
        $directory = sys_get_temp_dir().'/ezs-state-063-'.bin2hex(random_bytes(8));
        self::assertTrue(mkdir($directory));
        $path = $directory.'/desired.json';
        try {
            $initial = new DesiredServiceState($path);
            $initial->set('root',DesiredServiceState::RUNNING);
            $initial->set('lab',DesiredServiceState::RUNNING);
            $initial->set('lab',DesiredServiceState::STOPPED);
            $restored = new DesiredServiceState($path);
            self::assertSame(DesiredServiceState::RUNNING, $restored->get('root'));
            self::assertSame(DesiredServiceState::STOPPED, $restored->get('lab'));
            self::assertSame(DesiredServiceState::STOPPED, $restored->get('prod'));
        } finally {
            foreach (glob($directory.'/*') ?: [] as $file) if (is_file($file)) unlink($file);
            rmdir($directory);
        }
    }
}
