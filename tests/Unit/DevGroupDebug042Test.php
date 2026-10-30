<?php

declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\DevGroupDebugController;
use PHPUnit\Framework\TestCase;

final class DevGroupDebug042Test extends TestCase
{
    public function testAccessRestrictedToLocalDev(): void
    {
        self::assertTrue(DevGroupDebugController::allowed('dev', '127.0.0.1', '127.0.0.1'));
        self::assertTrue(DevGroupDebugController::allowed('dev', 'localhost', '::1'));
        self::assertFalse(DevGroupDebugController::allowed('prod', 'localhost', '127.0.0.1'));
        self::assertFalse(DevGroupDebugController::allowed('dev', 'remote.example', '127.0.0.1'));
        self::assertFalse(DevGroupDebugController::allowed('dev', 'localhost', '192.168.1.2'));
    }

    public function testSummaryExposesOnlyGroupStateCategories(): void
    {
        $summary = DevGroupDebugController::summary([
            'root_php' => 'ATTESTED', 'root_caddy' => 'ATTESTED',
            'ezscore_dev' => 'ATTESTED', 'ezscore_preview' => 'ABSENT',
            'lab' => 'ATTESTED', 'assistant' => 'RECORDED_UNVERIFIED',
        ]);
        self::assertSame(['dev', 'lab', 'assistant'], array_keys($summary));
        self::assertSame(['ezscore_dev' => 'ATTESTED', 'ezscore_preview' => 'ABSENT'], $summary['dev']);
        self::assertSame(['lab' => 'ATTESTED'], $summary['lab']);
        self::assertSame(['assistant' => 'RECORDED_UNVERIFIED'], $summary['assistant']);
        self::assertArrayNotHasKey('root_php', $summary);
    }
}
