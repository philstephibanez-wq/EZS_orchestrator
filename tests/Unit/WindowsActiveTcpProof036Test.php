<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Ezs\Web\Module\Infrastructure\WindowsActiveTcpProof;
use PHPUnit\Framework\TestCase;
final class WindowsActiveTcpProof036Test extends TestCase
{
    public function testExactFourTupleOwner():void
    {
        $net="  TCP 127.0.0.1:8791 127.0.0.1:50003 ESTABLISHED 12584\r\n"
            ."  TCP 127.0.0.1:8791 127.0.0.1:50004 ESTABLISHED 999\r\n";
        self::assertSame(12584,WindowsActiveTcpProof::parseOwner($net,8791,50003));
        self::assertNull(WindowsActiveTcpProof::parseOwner($net,8791,50005));
        self::assertNull(WindowsActiveTcpProof::parseOwner($net,8790,50003));
    }
    public function testRefusesAmbiguousForeignAndUnestablished():void
    {
        self::assertNull(WindowsActiveTcpProof::parseOwner("TCP 127.0.0.1:8791 127.0.0.1:50003 ESTABLISHED 0",8791,50003));
        self::assertNull(WindowsActiveTcpProof::parseOwner("TCP 127.0.0.1:8791 127.0.0.1:50003 TIME_WAIT 12584",8791,50003));
        self::assertNull(WindowsActiveTcpProof::parseOwner("TCP 127.0.0.1:8791 127.0.0.1:50003 ESTABLISHED 12584\nTCP 127.0.0.1:8791 127.0.0.1:50003 ESTABLISHED 999",8791,50003));
        self::assertNull(WindowsActiveTcpProof::parseOwner("TCP 0.0.0.0:8791 127.0.0.1:50003 ESTABLISHED 12584",8791,50003));
    }
    public function testNativeAttestationStillRejectsWrongPidAndCommand():void
    {
        $spec=NativeWindowsLifecycle::specs()['root_php'];
        $record=['pid'=>12584,'created'=>'20261030010000.000000+060'];
        $process=['pid'=>12584,'created'=>$record['created'],'executable'=>$spec['exe'],
           'command'=>'"'.$spec['exe'].'" "-b" "127.0.0.1:8791"'];
        self::assertTrue(NativeWindowsLifecycle::attest($record,$spec,$process,[8791=>[12584]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,$process,[8791=>[999]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$process,'command'=>'bad'],[8791=>[12584]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$process,'created'=>'other'],[8791=>[12584]]));
    }
}
