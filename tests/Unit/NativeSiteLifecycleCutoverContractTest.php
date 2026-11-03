<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\NativeSiteLifecycle;
use PHPUnit\Framework\TestCase;
final class NativeSiteLifecycleCutoverContractTest extends TestCase
{
    public function testPreflightBeforeNativeStart(): void
    {
        $seen=[];
        $adapter=new NativeSiteLifecycle(static function(array $args)use(&$seen):array{
            $site=$args[array_search('-Site',$args,true)+1];
            $action=$args[array_search('-Action',$args,true)+1];
            $seen[]=$action;
            return ['exit_code'=>0,'stdout'=>'EZS_PLATFORM_'.strtoupper($site).'_'.strtoupper($action).'_OK','stderr'=>''];
        });
        self::assertSame(['dev'=>'START_REQUESTED'],$adapter->start('dev'));
        self::assertSame(['Preflight','Start'],$seen);
    }
    public function testAssistantDelegatesCanonicallyButProdStopIsProtected(): void
    {
        $args=NativeSiteLifecycle::arguments('assistant','Start');
        self::assertSame('assistant',$args[array_search('-Site',$args,true)+1]);
        $this->expectException(RuntimeException::class);
        NativeSiteLifecycle::arguments('prod','Stop');
    }
    public function testNativeFailureDoesNotExposeRawSubprocessOutput(): void
    {
        $adapter=new NativeSiteLifecycle(static fn(array $args):array=>[
            'exit_code'=>1,'stdout'=>'','stderr'=>'DEV_MEDIA_ROOT_ENV_MISSING password=secret',
        ]);
        try {$adapter->request('dev','Start');self::fail('Must refuse');}
        catch(RuntimeException $e){
            self::assertStringContainsString('DEV_MEDIA_ROOT_ENV_MISSING',$e->getMessage());
            self::assertStringNotContainsString('secret',$e->getMessage());
        }
    }
    public function testMissingSuccessMarkerMustFailClosed():void
    {
        $adapter=new NativeSiteLifecycle(static fn(array $args):array=>['exit_code'=>0,'stdout'=>'unattested','stderr'=>'']);
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('EZS_NATIVE_SITE_UNATTESTED_SUCCESS');
        $adapter->request('lab','Status');
    }
    public function testSupervisorNoLongerCallsLegacyLifecycle():void
    {
        $code=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/ServiceSupervisorCommand.php');
        self::assertStringContainsString('NativeSiteLifecycle',$code);
        self::assertStringNotContainsString('NativeWindowsLifecycle',$code);
        self::assertStringContainsString('EZS_LEGACY_SUPERVISOR_TICK_RETIRED',$code);
    }
}
