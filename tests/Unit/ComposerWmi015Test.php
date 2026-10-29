<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class ComposerWmi015Test extends TestCase
{
    public function testNativeWindowsCommandsLoadComWithoutLegacyEntrypoints():void
    {
        $root=dirname(__DIR__,2);
        $composer=json_decode((string)file_get_contents($root.'/composer.json'),true,512,JSON_THROW_ON_ERROR);
        self::assertArrayNotHasKey('status',$composer['scripts']);
        foreach(['start','stop','ezs-status'] as $action){
            self::assertArrayHasKey($action,$composer['scripts']);
            self::assertStringContainsString('extension=H:/PHP/php-8.5-x64/ext/php_com_dotnet.dll',$composer['scripts'][$action]);
            self::assertStringNotContainsString('powershell',strtolower($composer['scripts'][$action]));
        }
        self::assertArrayHasKey('test',$composer['scripts']);
    }
}
