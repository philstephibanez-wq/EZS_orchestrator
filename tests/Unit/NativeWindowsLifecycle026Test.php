<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Symfony\Component\Console\Output\BufferedOutput;
use Ezs\Web\Module\Infrastructure\EcosystemEntryCommand;
final class NativeWindowsLifecycle026Test extends TestCase
{
    public function testNoPowerShellInNativeEngine():void {
        $s=file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/EcosystemEntryCommand.php');
        self::assertStringNotContainsString('powershell',strtolower(str_replace('sans PowerShell','',$s)));
        self::assertStringNotContainsString('scripts/start.ps1',$s);
    }
    public function testFullIdentityAttestationRequired():void {
        $spec=NativeWindowsLifecycle::specs()['root_php'];
        $process=['pid'=>45,'created'=>'20261029201215.000000+060','executable'=>$spec['exe'],'command'=>'"'.$spec['exe'].'" '.$spec['args']];
        $record=['pid'=>45,'created'=>$process['created']];
        self::assertTrue(NativeWindowsLifecycle::attest($record,$spec,$process,[8791=>[45]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,$process,[8791=>[]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,$process,[8791=>[46]]));
        self::assertFalse(NativeWindowsLifecycle::attest(['pid'=>45,'created'=>''], $spec,$process,[8791=>[45]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$process,'created'=>'other'],[8791=>[45]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$process,'executable'=>'C:/foreign/php-cgi.exe'],[8791=>[45]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$process,'command'=>'-b 127.0.0.1:87910'],[8791=>[45]]));
    }
    public function testCommandsRejectUnsupportedAndPlanIsSafe():void {
        $o=new BufferedOutput();self::assertSame(2,EcosystemEntryCommand::invoke('prod-stop',false,$o));
        $o=new BufferedOutput();self::assertSame(0,EcosystemEntryCommand::invoke('start',true,$o));
        self::assertStringContainsString('NATIVE_WINDOWS_WMI',$o->fetch());
    }
    public function testOnlyDevPortsIncluded():void {
        $ports=array_column(NativeWindowsLifecycle::specs(),'port');
        foreach([8501,8510,8511,8512] as $port)self::assertNotContains($port,$ports);
    }
}
