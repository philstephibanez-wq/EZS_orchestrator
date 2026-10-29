<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
final class NativeWindowsRecovery027Test extends TestCase
{
    public function testAllSixDevComponentsAreDefinedWithDistinctPorts():void
    {
        $spec=NativeWindowsLifecycle::specs();
        self::assertCount(6,$spec);
        self::assertSame(6,count(array_unique(array_column($spec,'port'))));
        foreach($spec as $item){self::assertStringStartsWith('H:/',$item['exe']);}
    }
    public function testWindowsIdentityRequiresNonemptyCreationDate():void
    {
        $s=NativeWindowsLifecycle::specs()['lab'];
        $proc=['pid'=>999,'created'=>'20261029155555.100000+060','executable'=>$s['exe'],'command'=>'"'.$s['exe'].'" '.$s['args']];
        self::assertTrue(NativeWindowsLifecycle::attest(['pid'=>999,'created'=>$proc['created']],$s,$proc,[8701=>[999]]));
        self::assertFalse(NativeWindowsLifecycle::attest(['pid'=>999,'created'=>''], $s,$proc,[8701=>[999]]));
        self::assertFalse(NativeWindowsLifecycle::attest(['pid'=>999,'created'=>'wrong'], $s,$proc,[8701=>[999]]));
    }
    public function testNativeStartupNeverIncludesProductionPorts():void
    {
        $ports=array_column(NativeWindowsLifecycle::specs(),'port');
        foreach([8501,8510,8511,8512] as $port)self::assertNotContains($port,$ports);
    }
    public function testLegacyScriptsAreNotRequiredByCommand():void
    {
        $src=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/EcosystemEntryCommand.php');
        self::assertStringNotContainsString('powershell.exe',$src);
        self::assertStringNotContainsString('.ps1',$src);
        self::assertStringContainsString('NativeWindowsLifecycle',$src);
    }
}
