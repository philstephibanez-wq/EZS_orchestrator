<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class BootGuard016Test extends TestCase
{
    public function testStartDoesNotInvokeGlobalStaleCleanup(): void
    {
        $s=(string)file_get_contents(dirname(__DIR__,2).'/scripts/start.ps1');
        self::assertStringNotContainsString('EZS_R3_ROOT_STATE_AMBIGUOUS_GLOBAL_CLEANUP',$s);
        self::assertStringNotContainsString('EZS_R13_REFUSED_AMBIGUOUS_GLOBAL_RECOVERY',$s);
        self::assertStringContainsString('Invoke-EzsRootLifecycle -Action start',$s);
    }
    public function testNewRootFastcgiPersistsWmiTimestamp(): void
    {
        $s=(string)file_get_contents(dirname(__DIR__,2).'/scripts/stop.ps1');
        self::assertStringContainsString('php_created_wmi = $backendCreated',$s);
        self::assertStringContainsString('caddy_created_wmi = $edgeCreated',$s);
        self::assertSame(2,substr_count($s,'$s.php_created_wmi = [string]$createdInfo.CreationDate'));
    }
    public function testProductionNotReferencedByNewStartGuard(): void
    {
        $s=(string)file_get_contents(dirname(__DIR__,2).'/scripts/start.ps1');
        self::assertStringContainsString('la reprise globale n\'est pas un preflight de START',$s);
    }
}
