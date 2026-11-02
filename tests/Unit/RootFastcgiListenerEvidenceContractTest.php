<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiListenerEvidenceContractTest extends TestCase
{
    public function testRefusalReportsListenerAndDoesNotWeakenGuard(): void
    {
        $script = file_get_contents(dirname(__DIR__, 2).'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($script);
        self::assertStringContainsString('ROOT_RECOVERY_LISTENER_EVIDENCE endpoint=', $script);
        self::assertStringContainsString('ROOT_RECOVERY_REFUSED_LISTENER_NETSTAT', $script);
        self::assertStringContainsString('ROOT_RECOVERY_REFUSED_REATTESTATION', $script);
        self::assertStringContainsString('ROOT_RECOVERY_REFUSED_DESIRED_STATE_MISSING', $script);
        self::assertStringContainsString('CADDY_DEV_HTTP_TIMEOUT_OWNED_PROCESS_NO_STOP_SECONDS', $script);
        self::assertSame(1, substr_count($script, 'ROOT_RECOVERY_LISTENER_EVIDENCE endpoint='));
        self::assertStringContainsString('if ($rootListening.Count -gt 0)', $script);
    }
}
