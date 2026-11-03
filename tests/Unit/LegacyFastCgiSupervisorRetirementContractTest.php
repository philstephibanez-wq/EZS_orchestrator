<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class LegacyFastCgiSupervisorRetirementContractTest extends TestCase
{
    public function testLegacyEntrypointCannotReachHistoricProcessLaunches(): void
    {
        $script = file_get_contents(dirname(__DIR__, 2).'/scripts/ezs_supervisor_tick.ps1');
        self::assertIsString($script);
        self::assertMatchesRegularExpression(
            '/\A\[CmdletBinding\(\)\]\r?\nparam\(\[switch\]\$DevOnly,\[switch\]\$RootOnly\)\r?\n'.
            '(?:(?!\breturn\b).)*EZS_LEGACY_CADDY_FASTCGI_ENTRYPOINT_RETIRED\x27\r?\nreturn\r?\n/s',
            $script
        );
        $guard = strpos($script, "Write-Output 'EZS_LEGACY_CADDY_FASTCGI_ENTRYPOINT_RETIRED'");
        $return = preg_match('/\r?\nreturn\r?\n/', $script, $match, PREG_OFFSET_CAPTURE, $guard)
            ? $match[0][1]
            : false;
        $spawn = strpos($script, 'Start-Process -FilePath $phpCgi');
        self::assertNotFalse($return);
        self::assertNotFalse($spawn);
        self::assertLessThan($spawn, $return);
    }
}
