<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
final class NativeArgumentBoundary028Test extends TestCase
{
    public function testExactPortMustHaveArgumentBoundary():void
    {
        $spec=NativeWindowsLifecycle::specs()['root_php'];
        $p=['pid'=>10,'created'=>'20261029210000','executable'=>$spec['exe'],'command'=>'"'.$spec['exe'].'" '.$spec['args']];
        $state=['pid'=>10,'created'=>$p['created']];
        self::assertTrue(NativeWindowsLifecycle::attest($state,$spec,$p,[8791=>[10]]));
        foreach(['0','01','-foreign'] as $suffix){
            self::assertFalse(NativeWindowsLifecycle::attest($state,$spec,[...$p,'command'=>$p['command'].$suffix],[8791=>[10]]));
        }
        self::assertFalse(NativeWindowsLifecycle::attest($state,$spec,[...$p,'command'=>'not the same command'],[8791=>[10]]));
    }
}
