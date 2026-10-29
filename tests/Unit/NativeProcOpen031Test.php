<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
final class NativeProcOpen031Test extends TestCase
{
    public function testAllSixSpecsAreSupportedWithoutShell():void
    {
        $specs=NativeWindowsLifecycle::specs();
        self::assertCount(6,$specs);
        foreach($specs as $spec){
            $argv=NativeWindowsLifecycle::spawnArguments($spec['args']);
            self::assertNotEmpty($argv);
            self::assertNotContains('cmd.exe',$argv);
            self::assertNotContains('powershell.exe',$argv);
        }
    }
    public function testArgumentInjectionRejected():void
    {
        foreach(['-b 127.0.0.1:8791 & echo test','-b 127.0.0.1:8791X',
                  'run --config foo --adapter caddyfile'] as $bad){
            try{NativeWindowsLifecycle::spawnArguments($bad);self::fail('Accepted unsafe args');}
            catch(\InvalidArgumentException $e){self::assertSame('EZS_PROC_ARGS_REFUSED',$e->getMessage());}
        }
    }
    public function testNativeLaunchUsesProcOpenAndDoesNotReintroducePowerShell():void
    {
        $text=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString('proc_open($command, $descriptors, $pipes, $cwd, null, [',$text);
        self::assertStringContainsString("'bypass_shell' => true",$text);
        self::assertStringContainsString("'create_new_console' => false",$text);
        self::assertStringNotContainsString('ExecMethod(', $text);
        self::assertStringNotContainsString('Win32_ProcessStartup',$text);
        self::assertStringContainsString('proc_get_status($resource)', $text);
    }
}
