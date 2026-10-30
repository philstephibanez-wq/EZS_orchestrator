<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Ezs\Web\Module\Infrastructure\SymfonyDevCachePreparation;
use PHPUnit\Framework\TestCase;
final class SymfonyDevCachePreparation039Test extends TestCase
{
    private static function states(string $default='ATTESTED'):array
    {
        return array_fill_keys(array_keys(NativeWindowsLifecycle::specs()),$default);
    }
    public function testAlreadyActiveDevDoesNotClearCache():void
    {
        self::assertSame([],SymfonyDevCachePreparation::rootsToPrepare(self::states(),NativeWindowsLifecycle::specs()));
    }
    public function testOnlyAbsentBackendsAndUniqueRootArePrepared():void
    {
        $states=self::states();
        $states['ezscore_dev']='ABSENT';
        $states['ezscore_preview']='ABSENT';
        $states['assistant']='ABSENT';
        self::assertSame(['H:/EZScore_dev','H:/EZStudioLab_assistant'],SymfonyDevCachePreparation::rootsToPrepare($states,NativeWindowsLifecycle::specs()));
    }
    public function testForeignOrUnverifiedPortNeverPreparesCache():void
    {
        foreach(['PORT_UNVERIFIED','RECORDED_UNVERIFIED'] as $state){
            $states=self::states();$states['ezscore_dev']=$state;
            try{SymfonyDevCachePreparation::rootsToPrepare($states,NativeWindowsLifecycle::specs());self::fail('Expected refusal');}
            catch(\RuntimeException $e){self::assertStringContainsString('EZS_CACHE_START_REFUSED_UNVERIFIED',$e->getMessage());}
        }
    }
    public function testCachePreparationIsDeduplicatedAndFailureStopsSequence():void
    {
        $called=[];
        try{
            SymfonyDevCachePreparation::prepare(['H:/EZScore_dev','H:/EZStudio_lab'],static function(string $root) use (&$called):void {
                $called[]=$root;
                throw new \RuntimeException('CACHE_FAILED');
            });
            self::fail('Expected failure');
        }catch(\RuntimeException $e){self::assertSame('CACHE_FAILED',$e->getMessage());}
        self::assertSame(['H:/EZScore_dev'],$called);
    }
    public function testProductionRootIsForbidden():void
    {
        $this->expectExceptionMessage('EZS_CACHE_ROOT_NOT_ALLOWED');
        SymfonyDevCachePreparation::prepare(['H:/EZScore'],static fn(string $root)=>null);
    }
}
