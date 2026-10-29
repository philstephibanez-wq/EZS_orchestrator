<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class BootStartReal021Test extends TestCase
{
    private static function source(string $name): string
    {
        return (string) file_get_contents(dirname(__DIR__, 2) . '/scripts/' . $name . '.ps1');
    }

    public function testActualStartEngineHasStaleRecoveryGuard(): void
    {
        $start = self::source('start');
        self::assertSame(1, substr_count($start, '# EZS_DEV_STALE_R2: transactional restoration'));
        self::assertStringContainsString('Invoke-EzsRootLifecycle -Action start', $start);
    }

    public function testGuardMatchesSourceInStopAndPrecedesStateRead(): void
    {
        $start = self::source('start');
        $stop = self::source('stop');
        $marker = '# EZS_DEV_STALE_R2: transactional restoration';
        $beginA = strpos($start, $marker);
        $beginB = strpos($stop, $marker);
        self::assertNotFalse($beginA);
        self::assertNotFalse($beginB);
        $endA = strpos($start, '    $s = State', $beginA);
        $endB = strpos($stop, '    $s = State', $beginB);
        self::assertSame(substr($stop, $beginB, $endB-$beginB), substr($start, $beginA, $endA-$beginA));
    }

    public function testCannotArchiveWhenRecordedProcessLives(): void
    {
        $source = self::source('start');
        self::assertStringContainsString('EZS_R2_STALE_RECOVERY_REFUSED_RECORDED_PID_ACTIVE_', $source);
        self::assertStringContainsString('EZS_R2_STALE_RECOVERY_REFUSED_PORT_ACTIVE_', $source);
        self::assertStringContainsString('Move-Item -LiteralPath $stateFile', $source);
    }

    public function testNoProdStateMutationInGuard(): void
    {
        $start = self::source('start');
        $b = strpos($start, '# EZS_DEV_STALE_R2: transactional restoration');
        $e = strpos($start, '    $s = State', $b);
        $guard = substr($start, $b, $e-$b);
        self::assertStringNotContainsString('v2-prod', $guard);
        self::assertStringNotContainsString('Stop-Process', $guard);
        self::assertStringContainsString('H:\\temp\\ezs-orchestrator\\stale-root-state', $guard);
    }
}
