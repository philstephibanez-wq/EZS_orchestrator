<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\RootHealthDecision;
use PHPUnit\Framework\TestCase;

final class RootHealthDecision064Test extends TestCase
{
    public function testStatelessDecisionAcrossAllRootStates(): void
    {
        foreach ([null, 0, 502, 503, 404, 301] as $code) {
            self::assertSame('ROOT_RECOVERY_REQUIRED', RootHealthDecision::decide($code, true));
            self::assertSame('ROOT_STOPPED_BY_OPERATOR', RootHealthDecision::decide($code, false));
        }
        self::assertSame('ROOT_HEALTHY', RootHealthDecision::decide(200, true));
        self::assertSame('ROOT_STOPPED_BY_OPERATOR', RootHealthDecision::decide(200, false));
    }
}
