<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use Ezs\Web\Module\Infrastructure\IncidentRegisterR6 as R;
use PHPUnit\Framework\TestCase;
final class IncidentRegisterR6Test extends TestCase
{
    public function testAbaIsDeduplicatedAndResolutionReopensIncident(): void
    {
        $r=[];$t='2026-11-03T20:00:00Z';
        self::assertNotNull(R::transition($r,'prod','soft','FATAL','404','A',$t));
        self::assertNull(R::transition($r,'prod','soft','FATAL','404','A',$t));
        self::assertNotNull(R::transition($r,'prod','soft','FATAL','404','B',$t));
        self::assertNull(R::transition($r,'prod','soft','FATAL','404','A',$t));
        self::assertNotNull(R::transition($r,'prod','soft','OK','OK','OK',$t));
        self::assertNull(R::transition($r,'prod','soft','OK','OK','OK',$t));
        self::assertNotNull(R::transition($r,'prod','soft','FATAL','404','A',$t));
    }
    public function testFingerprintsAreStableForWhitespace(): void
    {
        self::assertSame(R::fingerprint('prod','soft','ERROR','E','Hello world'),R::fingerprint('prod','soft','ERROR','E'," Hello   world "));
    }
}
