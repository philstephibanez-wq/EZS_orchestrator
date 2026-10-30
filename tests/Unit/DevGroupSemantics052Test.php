<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class DevGroupSemantics052Test extends TestCase
{
    public function testCommandsDoNotChangeNativePermissionsAndUseSemanticColours(): void
    {
        $root = dirname(__DIR__, 2);
        $js = (string) file_get_contents($root.'/public/assets/ezs-infrastructure.js');
        $css = (string) file_get_contents($root.'/public/assets/ezs-debug-layout.css');
        $diagnostic = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString("state.state === 'RUNNING' && state.restart === true", $js);
        self::assertStringContainsString("state.state === 'STOPPED' && state.start === true", $js);
        self::assertStringContainsString('Vérification…', $js);
        self::assertStringContainsString('data-ezs-state-probe-ms', $js);
        self::assertStringContainsString('Commandes natives disponibles', $js);
        self::assertStringContainsString('data-ezs-state="STOPPED"', $css);
        self::assertStringContainsString('background: #a72432', $css);
        self::assertStringContainsString('item?.restart === true', $diagnostic);
        self::assertStringContainsString('attente permissions ms=', $diagnostic);
        self::assertStringNotContainsString("if (d.start !== String(item?.start !== true))", $diagnostic);
        self::assertSame(0, preg_match('/\bmethod\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\']/i', $diagnostic));
    }
}
