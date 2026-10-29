<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class LaAttestation022Test extends TestCase
{
    private static function startScript(): string
    {
        $file = dirname(__DIR__,2).'/scripts/start.ps1';
        self::assertFileExists($file);
        return (string)file_get_contents($file);
    }

    public function testLabIdentityIsRetriedWithoutChangingItsStrictAttestation(): void
    {
        $s=self::startScript();
        self::assertStringContainsString('for($laIdentityAttempt=0;$laIdentityAttempt -lt 20;$laIdentityAttempt++)', $s);
        self::assertStringContainsString('if(Attested $p.port $p.pid $stamp){$laIdentityOk=$true;break}', $s);
        self::assertStringContainsString('if(-not $laIdentityOk)', $s);
    }

    public function testFailureRetainsRefusalAndObservability(): void
    {
        $s=self::startScript();
        self::assertStringContainsString('EZS_LA_ATTEST_DIAGNOSTIC', $s);
        self::assertStringContainsString("throw 'EZS_LA_START_NOT_ATTESTED'", $s);
        self::assertStringContainsString('creation_matches=', $s);
    }

    public function testProductionIsAbsentFromTheReplacementSection(): void
    {
        $s=self::startScript();
        $a=strpos($s,'# After TCP readiness, WMI and the ownership snapshot may still settle.');
        $b=strpos($s,'$records+=@{pid=$p.pid;stamp=$stamp}', $a);
        self::assertNotFalse($a); self::assertNotFalse($b);
        $patch=substr($s,$a,$b-$a);
        self::assertStringNotContainsString('v2-prod', $patch);
        self::assertStringNotContainsString('Stop-Process', $patch);
        self::assertStringNotContainsString('Remove-Item', $patch);
    }
}
