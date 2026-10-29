<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class DevStaleBoot017Test extends TestCase
{
    private static function script(): string
    {
        return (string) file_get_contents(dirname(__DIR__, 2) . '/scripts/stop.ps1');
    }

    public function testStaleRecoveryIsRestrictedToStart(): void
    {
        self::assertStringContainsString("if (\$Action -eq 'start' -and (Test-Path", self::script());
    }

    public function testRecordedLiveProcessBlocksStateRecovery(): void
    {
        self::assertStringContainsString('EZS_R2_STALE_RECOVERY_REFUSED_RECORDED_PID_ACTIVE_', self::script());
        self::assertStringContainsString('ProcessInfo $rootPid', self::script());
    }

    public function testActiveListenerBlocksStateRecovery(): void
    {
        self::assertStringContainsString('EZS_R2_STALE_RECOVERY_REFUSED_PORT_ACTIVE_', self::script());
        self::assertStringContainsString('@(8790,8791,8502,8852)', self::script());
    }

    public function testArchiveRetainsEvidenceOutsideRepository(): void
    {
        self::assertStringContainsString('H:\\temp\\ezs-orchestrator\\stale-root-state', self::script());
        self::assertStringContainsString('Move-Item -LiteralPath $stateFile -Destination $destination', self::script());
    }

    public function testNoProdStateMutationAdded(): void
    {
        $s = self::script();
        self::assertStringNotContainsString('Remove-Item -LiteralPath $root', $s);
        self::assertStringContainsString('EZS_R2_STALE_DEV_COLD_START_ALLOWED', $s);
    }
}
