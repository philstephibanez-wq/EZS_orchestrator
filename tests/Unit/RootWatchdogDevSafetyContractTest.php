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
        // Scope to the Caddy loop: ROOT FastCGI has its own, earlier stop action.
        $loopAt = strpos($code, 'foreach ($spec in $specs)');
        self::assertNotFalse($loopAt);
        $caddyLoop = substr($code, $loopAt);
        self::assertStringContainsString("Name='prod'", $code);
        self::assertStringContainsString("if (\$name -eq 'dev' -and \$owned.Count -gt 0)", $caddyLoop);
        self::assertStringContainsString('CADDY_DEV_HTTP_TIMEOUT_OWNED_PROCESS_NO_STOP_SECONDS=', $caddyLoop);
        $guard = strpos($caddyLoop, "if (\$name -eq 'dev' -and \$owned.Count -gt 0)");
        $kill = strpos($caddyLoop, 'Stop-Process -Id $pidToStop -Force');
        self::assertNotFalse($guard);
        self::assertNotFalse($kill);
        self::assertLessThan($kill, $guard);
    }
}
