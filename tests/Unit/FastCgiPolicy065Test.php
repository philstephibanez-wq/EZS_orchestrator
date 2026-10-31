<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\FastCgiPolicy;
use PHPUnit\Framework\TestCase;
final class FastCgiPolicy065Test extends TestCase
{
    public function testOnlyExpectedFastCgiAreManaged(): void
    {
        self::assertTrue(FastCgiPolicy::isFastCgi('lab'));
        self::assertTrue(FastCgiPolicy::isFastCgi('prod_gateway'));
        self::assertFalse(FastCgiPolicy::isFastCgi('root_caddy'));
        self::assertFalse(FastCgiPolicy::isFastCgi('root_php'));
    }
    public function testNeverRecoverStoppedOrHealthyService(): void
    {
        self::assertFalse(FastCgiPolicy::shouldRecover(false,false,null,100));
        self::assertFalse(FastCgiPolicy::shouldRecover(true,true,0,100));
        self::assertFalse(FastCgiPolicy::shouldRecover(true,false,50,100));
        self::assertTrue(FastCgiPolicy::shouldRecover(true,false,40,100));
    }
}
