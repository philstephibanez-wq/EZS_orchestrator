<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class DevGroupLoading053Test extends TestCase
{
    public function testSpinnerIsOnlyPresentDuringUnverifiedState(): void
    {
        $root = dirname(__DIR__, 2);
        $js = (string) file_get_contents($root.'/public/assets/ezs-infrastructure.js');
        $css = (string) file_get_contents($root.'/public/assets/ezs-debug-layout.css');

        self::assertStringContainsString('spinner-border spinner-border-sm ezs-command-spinner', $js);
        self::assertStringContainsString('aria-hidden="true"', $js);
        self::assertStringContainsString('$button.prop(\'disabled\', true).attr(\'aria-busy\', \'true\').html(checkingMarkup)', $js);
        self::assertStringContainsString("if (!modes[group]) checking(controls[group].start)", $js);
        self::assertStringContainsString("controls[group].start.removeAttr('aria-busy')", $js);
        self::assertStringContainsString("state.state === 'RUNNING' && state.restart === true", $js);
        self::assertStringContainsString("state.state === 'STOPPED' && state.start === true", $js);
        self::assertStringContainsString('animation: ezs-debug-rotate 0.7s linear infinite', $css);
        self::assertStringContainsString('.ezs-server-card:has(#assistant-title) .ezs-command-spinner', $css);
        self::assertStringNotContainsString("dev-groups/'+group+'/restart", $js);
    }
}
