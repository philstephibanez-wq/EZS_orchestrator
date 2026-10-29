<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class NativePendingGate032Test extends TestCase
{
    private string $directory;

    protected function setUp(): void
    {
        $this->directory=sys_get_temp_dir().'/ezs-r8f3-'.bin2hex(random_bytes(8));
        self::assertTrue(mkdir($this->directory));
    }

    protected function tearDown(): void
    {
        foreach (glob($this->directory.'/*') ?: [] as $file) unlink($file);
        rmdir($this->directory);
    }

    public function testPendingCreationRefusesStartAndStopWithoutProcessMutation():void
    {
        file_put_contents($this->directory.'/native-spawn-pending.json','{"schema":"ezs.native.pending.v1"}');
        $calls=0;
        $service=new NativeWindowsLifecycle(
            static function():array {return [];},
            static function():array {return [];},
            static function() use (&$calls):int {$calls++;return 999;},
            static function() use (&$calls):bool {$calls++;return true;},
            $this->directory
        );
        foreach (['start','stop','status'] as $action) {
            try {$service->$action();self::fail('Operation accepted with pending intent');}
            catch (\RuntimeException $e) {
                self::assertSame('EZS_NATIVE_PENDING_REQUIRES_MANUAL_ATTESTATION',$e->getMessage());
            }
        }
        self::assertSame(0,$calls);
        self::assertFileExists($this->directory.'/native-spawn-pending.json');
    }

    public function testAbsentDependencyRefusesWithoutSpawning():void
    {
        $calls=0;
        $service=new NativeWindowsLifecycle(
            static fn():array=>[],static fn():array=>[],
            static function() use (&$calls):int {$calls++;return 999;},
            static fn(int $pid):bool=>true,$this->directory,
            static fn(string $exe,string $cwd):bool=>$cwd !== 'H:/EZScore_dev'
        );
        try {$service->start();self::fail('Expected preflight to refuse missing dependency');}
        catch (\RuntimeException $e) {
            self::assertStringStartsWith('EZS_NATIVE_DEPENDENCY_MISSING_',$e->getMessage());
        }
        self::assertSame(0,$calls);
        self::assertFileDoesNotExist($this->directory.'/native-spawn-pending.json');
    }
}
