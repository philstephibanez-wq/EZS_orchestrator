<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\NativeSiteObservation;
use PHPUnit\Framework\TestCase;

final class NativeSiteRestCutoverR4Test extends TestCase
{
    public function testColdAndRunningObservationsAreBounded(): void
    {
        self::assertSame(['state'=>'STOPPED','start'=>true,'stop'=>false,'restart'=>false,'desired'=>'STOPPED'],
            NativeSiteObservation::classify('dev',"SITE=dev INTENT=STOPPED OWNED=0 LISTENERS=0\nEZS_PLATFORM_DEV_STATUS_OK\n"));
        self::assertSame(['state'=>'RUNNING','start'=>false,'stop'=>true,'restart'=>true,'desired'=>'RUNNING'],
            NativeSiteObservation::classify('lab',"SITE=lab INTENT=RUNNING OWNED=1 LISTENERS=2\nEZS_PLATFORM_LAB_STATUS_OK\n"));
    }

    public function testAmbiguousAndForeignObservationAreBlocked(): void
    {
        foreach (["SITE=dev INTENT=RUNNING OWNED=2 LISTENERS=2\n", "SITE=dev INTENT=RUNNING OWNED=0 LISTENERS=1\n"] as $raw) {
            $result=NativeSiteObservation::classify('dev',$raw);
            self::assertSame('UNVERIFIED',$result['state']);
            self::assertFalse($result['start']);
            self::assertFalse($result['stop']);
            self::assertFalse($result['restart']);
        }
    }

    public function testWrongSiteAndDuplicateEvidenceAreRejected(): void
    {
        foreach (["SITE=lab INTENT=RUNNING OWNED=1 LISTENERS=2", "SITE=dev INTENT=RUNNING OWNED=1 LISTENERS=2\nSITE=dev INTENT=RUNNING OWNED=1 LISTENERS=2"] as $raw) {
            try {
                NativeSiteObservation::classify('dev',$raw);
                self::fail('Untrusted evidence must be refused');
            } catch (RuntimeException $expected) {
                self::assertStringStartsWith('EZS_NATIVE_OBSERVATION_', $expected->getMessage());
            }
        }
    }

    public function testRestControllerCannotInvokeLegacyFastCgiAndAssistantUsesNativeBridge(): void
    {
        $root=dirname(__DIR__,2);
        foreach (['DevGroupOperationsController.php','DevGroupDebugController.php'] as $name) {
            $content=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/'.$name);
            self::assertStringNotContainsString('NativeWindowsLifecycle',$content);
            self::assertStringNotContainsString('reconcileFastCgiGroup',$content);
            self::assertStringNotContainsString('php-cgi.exe',$content);
        }
        $ops=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("if (!in_array(\$group,['dev','lab','assistant'],true))",$ops);
        self::assertStringContainsString('new NativeSiteLifecycle()', $ops);
        self::assertStringContainsString('restart_incomplete', $ops);
        self::assertStringContainsString('DesiredServiceState::STOPPED',$ops);
    }
}
