<?php
declare(strict_types=1);
use Ezs\Web\Module\Infrastructure\Controller\WebRecoveryPreflightController;
use PHPUnit\Framework\TestCase;

final class WebRecoveryPreflight080Test extends TestCase
{
    public function testRestrictedToLocalDev(): void
    {
        self::assertTrue(WebRecoveryPreflightController::allowed('dev','localhost','127.0.0.1'));
        self::assertFalse(WebRecoveryPreflightController::allowed('prod','localhost','127.0.0.1'));
        self::assertFalse(WebRecoveryPreflightController::allowed('dev','example.org','127.0.0.1'));
        self::assertFalse(WebRecoveryPreflightController::allowed('dev','localhost','192.0.2.1'));
    }
}
