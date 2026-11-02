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
        self::assertStringContainsString("controls[group].start.text('État inconnu')", $js);
        self::assertStringContainsString('data-ezs-state-probe-ms', $js);
        self::assertStringContainsString('Commandes natives disponibles', $js);
        self::assertStringContainsString('data-ezs-state="STOPPED"', $css);
        self::assertStringContainsString('background: #a72432', $css);
        self::assertStringContainsString("'data-ezs-state'", $diagnostic);
        self::assertStringContainsString("'data-ezs-probe'", $diagnostic);
        self::assertStringContainsString("method:'GET'", $diagnostic);
        self::assertStringNotContainsString('ÉCARTS API / DOM', $diagnostic);
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $diagnostic);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $diagnostic);
        self::assertStringContainsString("request:{method:'POST'", $diagnostic);
        self::assertStringContainsString("method:'GET'", $diagnostic);
        self::assertStringNotContainsString("fetch(url, {method:'POST'", $diagnostic);
    }
}
