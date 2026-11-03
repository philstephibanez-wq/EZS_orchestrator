<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeStopAttestationContractTest extends TestCase
{
    public function testLegacyLifecycleStillGuardsIdentityWhilePendingRemoval(): void
    {
        $source = (string)file_get_contents(dirname(__DIR__, 2).'/src/Module/Infrastructure/NativeWindowsLifecycle.php');
        self::assertStringContainsString("'C:/Windows/System32/taskkill.exe', '/PID'", $source);
        self::assertStringContainsString('EZS_FASTCGI_STOP_NOT_EXITED_', $source);
        self::assertStringContainsString('!isset($afterProcesses[$pid]) && !self::occupied($spec, $afterPorts)', $source);
        self::assertStringContainsString('EZS_FASTCGI_IDENTITY_CHANGED_', $source);
    }

    public function testNativeRestStopRequiresObservationBeforeSuccessOrRestart(): void
    {
        $source=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("'EZS_STOP_NOT_VERIFIED_'", $source);
        self::assertStringContainsString("'EZS_RESTART_STOP_NOT_VERIFIED'", $source);
        self::assertStringContainsString("'restart_incomplete'", $source);
        self::assertMatchesRegularExpression(
            '/\\$result = \\$native->stop\\(\\$group\\);\\s*if \\(\\$observation->observe\\(\\$group\\)\\[\\x27state\\x27\\] !== \\x27STOPPED\\x27\\)/',
            $source
        );
        self::assertMatchesRegularExpression(
            '/\\$stopped = \\$native->stop\\(\\$group\\);\\s*try \\{\\s*if \\(\\$observation->observe\\(\\$group\\)\\[\\x27state\\x27\\] !== \\x27STOPPED\\x27\\)/',
            $source
        );
    }
}
