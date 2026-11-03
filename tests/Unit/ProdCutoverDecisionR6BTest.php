<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Infrastructure\ProdCutoverDecisionR6B;
use PHPUnit\Framework\TestCase;

final class ProdCutoverDecisionR6BTest extends TestCase
{
    public function testOnlyConfirmedProdFatalInNormalModeIsCandidate(): void
    {
        $fatal = ['state'=>'FATAL','code'=>'SOFT_HTTP_404'];
        $closed = ['8501'=>'CLOSED','8510'=>'CLOSED','8511'=>'CLOSED'];
        self::assertTrue(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',$fatal,'ABSENT',$closed));
        self::assertTrue(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',$fatal,'ATTESTED',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',$fatal,'COUNTS_CONSISTENT_NOT_OWNER_ATTESTED',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('STOPPED','NORMAL',$fatal,'ABSENT',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('RUNNING','MAINTENANCE',$fatal,'ABSENT',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',['state'=>'ERROR','code'=>'SOFT_HTTP_500'],'ABSENT',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',$fatal,'UNVERIFIED',$closed));
        self::assertFalse(ProdCutoverDecisionR6B::eligible('RUNNING','NORMAL',$fatal,'ABSENT',['8501'=>'OPEN']));
    }
}
