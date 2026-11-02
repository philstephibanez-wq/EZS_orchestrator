<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructurePartialStopContractTest extends TestCase
{
    public function testPartialStateUsesServerStopPermission(): void
    {
        $source = file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertIsString($source);
        self::assertStringContainsString("stop:state.stop === true", $source);
        self::assertStringContainsString("controls[group].stop.prop('disabled', next.stop !== true)", $source);
        self::assertStringContainsString("data-ezs-stop-authorized", $source);
        self::assertStringContainsString("mode === null", $source);
    }
}
