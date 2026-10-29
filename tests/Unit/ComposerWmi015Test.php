<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class ComposerWmi015Test extends TestCase
{
    public function testOnlyStatusLoadsComAndScriptsAvoidReservedComposerNames(): void
    {
        $root = dirname(__DIR__, 2);
        $composer = json_decode((string) file_get_contents($root . '/composer.json'), true, 512, JSON_THROW_ON_ERROR);
        self::assertArrayNotHasKey('status', $composer['scripts']);
        self::assertSame('@php -d extension=H:/PHP/php-8.5-x64/ext/php_com_dotnet.dll bin/console ezs:ecosystem:status', $composer['scripts']['ezs-status']);
        self::assertArrayHasKey('start', $composer['scripts']);
        self::assertArrayHasKey('stop', $composer['scripts']);
        self::assertArrayHasKey('test', $composer['scripts']);
        self::assertStringNotContainsString('com_dotnet', json_encode($composer['scripts']['stop'], JSON_THROW_ON_ERROR));
    }
}
