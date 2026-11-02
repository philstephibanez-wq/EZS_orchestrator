<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class RootWatchdogDevSafetyContractTest extends TestCase
{
    public function testDevDoesNotKillIdentifiedCaddyOnlyBecauseHttpTimesOut(): void
    {
        $root = dirname(__DIR__, 2);
        $code = file_get_contents($root.'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($code);
        self::assertStringContainsString("if (\$name -eq 'dev' -and \$owned.Count -gt 0)", $code);
        self::assertStringContainsString('CADDY_DEV_HTTP_TIMEOUT_OWNED_PROCESS_NO_STOP_SECONDS=', $code);
        self::assertStringContainsString('Stop-Process -Id $pidToStop -Force', $code);
        self::assertStringContainsString("Name='prod'", $code);
        $guard = strpos($code, "if (\$name -eq 'dev' -and \$owned.Count -gt 0)");
        $kill = strpos($code, 'Stop-Process -Id $pidToStop -Force');
        self::assertNotFalse($guard);
        self::assertNotFalse($kill);
        self::assertLessThan($kill, $guard);
    }
}
