<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\NativeSiteObservation as Observer;
use PHPUnit\Framework\TestCase;

final class NativeObservationDiagnosticR6CTest extends TestCase
{
    public function testAbsentAllowsManualStartEvenWithPersistedRunningIntent(): void
    {
        $d=Observer::diagnose('dev',"SITE=dev INTENT=RUNNING OWNED=0 LISTENERS=0\n");
        self::assertSame('STOPPED',$d['state']);
        self::assertSame('NATIVE_ABSENCE_ATTESTED',$d['reason_code']);
        self::assertTrue($d['can_start']);
        self::assertFalse($d['can_stop']);
    }

    public function testListeningWithoutNativeOwnershipRemainsBlocked(): void
    {
        $d=Observer::diagnose('lab',"SITE=lab INTENT=RUNNING OWNED=0 LISTENERS=2\n");
        self::assertSame('UNVERIFIED',$d['state']);
        self::assertSame('LISTENERS_WITHOUT_NATIVE_PROCESS',$d['reason_code']);
        self::assertFalse($d['can_start']);
        self::assertFalse($d['can_stop']);
    }

    public function testNativeProcessAndPortMismatchAreNotAttested(): void
    {
        $d=Observer::diagnose('dev',"SITE=dev INTENT=RUNNING OWNED=1 LISTENERS=1\n");
        self::assertSame('NATIVE_LISTENER_COUNT_MISMATCH',$d['reason_code']);
        self::assertFalse($d['can_stop']);
        $d=Observer::diagnose('dev',"SITE=dev INTENT=RUNNING OWNED=2 LISTENERS=2\n");
        self::assertSame('MULTIPLE_NATIVE_PROCESSES',$d['reason_code']);
    }

    public function testKnownAttestedSiteRetainsExistingPermissionSemantics(): void
    {
        $raw="SITE=assistant INTENT=RUNNING OWNED=1 LISTENERS=3\n";
        self::assertSame('RUNNING',Observer::classify('assistant',$raw)['state']);
        self::assertTrue(Observer::diagnose('assistant',$raw)['can_stop']);
    }

    public function testForgedAndDuplicateEvidenceFailClosed(): void
    {
        $this->expectException(RuntimeException::class);
        Observer::diagnose('dev',"SITE=dev INTENT=RUNNING OWNED=0 LISTENERS=0\nSITE=dev INTENT=RUNNING OWNED=0 LISTENERS=0\n");
    }
}
