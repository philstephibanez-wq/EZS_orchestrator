<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\FastCgiProcessClassification as C;
use PHPUnit\Framework\TestCase;

final class FastCgiProcessClassification067Test extends TestCase
{
    public function testProcessClassificationIsConservative(): void
    {
        self::assertSame('ACTIVE', C::label(true, true));
        self::assertSame('RESIDUAL', C::label(true, false));
        self::assertSame('UNVERIFIED', C::label(false, true));
        self::assertSame('UNVERIFIED', C::label(false, false));
    }
}
