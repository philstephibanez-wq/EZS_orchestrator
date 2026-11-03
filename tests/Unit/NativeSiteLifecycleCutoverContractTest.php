<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\NativeSiteLifecycle;
use PHPUnit\Framework\TestCase;

final class NativeSiteLifecycleCutoverContractTest extends TestCase
{
    public function testCanonicalAdapterUsesAnArgumentVectorAndPreflightBeforeStart(): void
    {
        $seen=[];
        $adapter=new NativeSiteLifecycle(static function (array $args) use (&$seen): array {
            $seen[]=$args;
            $action=$args[array_search('-Action',$args,true)+1];
            return ['exit_code'=>0,'stdout'=>'EZS_PLATFORM_DEV_'.strtoupper($action).'_OK', 'stderr'=>''];
        });
        self::assertSame(['dev'=>'START_REQUESTED'],$adapter->start('dev'));
        self::assertCount(2,$seen);
        self::assertSame('Preflight',end($seen[0]));
        self::assertSame('Start',end($seen[1]));
        self::assertContains('ezs_platform_control.ps1',array_map('basename',$seen[0]));
        self::assertSame('powershell.exe',$seen[0][0]);
    }

    public function testNoAssistantOrProdStopDelegation(): void
    {
        foreach ([['assistant','Start'],['prod','Stop'],['unknown','Start']] as [$site,$action]) {
            try {
                NativeSiteLifecycle::arguments($site,$action);
                self::fail('Must refuse '.$site.' '.$action);
            } catch (\InvalidArgumentException|\RuntimeException $expected) {
                self::assertNotSame('', $expected->getMessage());
            }
        }
    }

    public function testMissingSuccessMarkerMustFailClosed(): void
    {
        $adapter=new NativeSiteLifecycle(static fn(array $args): array=>[
            'exit_code'=>0,'stdout'=>'process started without attestation','stderr'=>'',
        ]);
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('EZS_NATIVE_SITE_UNATTESTED_SUCCESS');
        $adapter->request('lab','Status');
    }

    public function testNativeFailureIsNotSwallowed(): void
    {
        $adapter=new NativeSiteLifecycle(static fn(array $args): array=>[
            'exit_code'=>1,'stdout'=>'','stderr'=>'unsafe process',
        ]);
        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('EZS_NATIVE_SITE_ACTION_FAILED_lab_Preflight_CODE_1');
        $adapter->request('lab','Preflight');
    }

    public function testPublishedSupervisorNoLongerReferencesLegacyLifecycle(): void
    {
        $root=dirname(__DIR__,2);
        $code=(string)file_get_contents($root.'/src/Module/Infrastructure/ServiceSupervisorCommand.php');
        self::assertStringContainsString('new NativeSiteLifecycle()',$code);
        self::assertStringNotContainsString('NativeWindowsLifecycle',$code);
        self::assertStringNotContainsString('reconcileFastCgiGroup',$code);
        self::assertStringNotContainsString('cleanupRootResidual',$code);
        self::assertStringNotContainsString('AssistantDependencyLifecycle',$code);
        self::assertStringContainsString('EZS_LEGACY_SUPERVISOR_TICK_RETIRED',$code);
        self::assertStringContainsString("!in_array(\$group,['dev','lab'],true)",$code);
    }
}
