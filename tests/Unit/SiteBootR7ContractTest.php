<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SiteBootR7ContractTest extends TestCase
{
    public function testBootstrapScopesAndSafety(): void
    {
        $root=dirname(__DIR__,2);
        $boot=(string)file_get_contents($root.'/scripts/ezs_boot_sites_r7.ps1');
        self::assertStringContainsString("@('dev','lab','assistant','prod')",$boot);
        self::assertStringContainsString("'SKIPPED_PROD_MAINTENANCE'",$boot);
        self::assertStringContainsString("'BLOCKED_AMBIGUOUS'",$boot);
        self::assertStringContainsString('EZS_R7_BOOT_LOCK_BUSY',$boot);
        self::assertStringContainsString('-Action Start',$boot);
        self::assertStringNotContainsString('desired-services.json',$boot);
        self::assertStringNotContainsString('Stop-Process',$boot);
    }
    public function testCanonicalNativeAndAssistantLifecyclesDoNotUsePersistedIntent(): void
    {
        $root=dirname(__DIR__,2);
        $native=(string)file_get_contents($root.'/scripts/ezs_native_site.ps1');
        $assistant=(string)file_get_contents($root.'/scripts/ezs_assistant_stack.ps1');
        foreach([$native,$assistant] as $src){
            self::assertStringNotContainsString('desired-services.json',$src);
            self::assertStringNotContainsString('Read-Desired',$src);
        }
        self::assertStringContainsString('PROCESS_IDENTITY_REATTEST_FAILED',$native);
        self::assertStringContainsString('PROD_STOP_PROTECTED_REFUSED',$native);
        self::assertStringContainsString('scripts\\start.ps1',$assistant);
        self::assertStringContainsString('scripts\\stop.ps1',$assistant);
    }
    public function testResidentBootsOnlyOnceAfterRootHealth(): void
    {
        $src=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_supervisor_resident.ps1');
        self::assertStringContainsString('if (!$attempted)', $src);
        self::assertStringContainsString('$attempted=$true',$src);
        self::assertStringContainsString('127.0.0.1:8790/health',$src);
        self::assertStringContainsString('-Action Boot',$src);
        self::assertStringNotContainsString('ezs_supervisor_tick.ps1',$src);
    }
}
