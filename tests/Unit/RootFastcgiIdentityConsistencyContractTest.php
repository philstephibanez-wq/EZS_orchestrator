<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiIdentityConsistencyContractTest extends TestCase
{
    public function testBothTerminationPathsAreGuarded(): void
    {
        $s = file_get_contents(__DIR__ . '/../../scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($s);
        self::assertStringContainsString('param([switch]$DevOnly,[switch]$RootOnly)', $s);
        self::assertStringContainsString('if ($RootOnly) { $specs = @() }', $s);
        self::assertStringContainsString('ROOT_RECOVERY_REFUSED_TCP_CONFLICT', $s);
        self::assertStringContainsString('Get-NetTCPConnection -LocalPort 8791 -ErrorAction Stop', $s);
        self::assertStringContainsString('ROOT_RECOVERY_REFUSED_FINAL_NETSTAT_LISTENER', $s);
        self::assertStringContainsString('ROOT_HEALTH_RECOVERY_REFUSED_FINAL_NETSTAT_OWNER', $s);
        self::assertSame(1, substr_count($s, 'Stop-Process -Id $targetPid -Force -ErrorAction Stop'));
        self::assertSame(2, substr_count($s, 'Stop-Process -Id $pidToStop -Force -ErrorAction Stop'));
        self::assertLessThan(
            strpos($s, 'Stop-Process -Id $pidToStop -Force -ErrorAction Stop'),
            strpos($s, 'ROOT_RECOVERY_REFUSED_TCP_CONFLICT')
        );
        self::assertLessThan(
            strpos($s, 'Stop-Process -Id $targetPid -Force -ErrorAction Stop'),
            strpos($s, 'ROOT_HEALTH_RECOVERY_REFUSED_FINAL_NETSTAT_OWNER')
        );
    }
}
