<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

/** A missing or unverified native attestation must never enable service controls. */
final class DevGroupLoading053Test extends TestCase
{
    public function testControlsStayDisabledUntilTheServerAttestsPermissions(): void
    {
        $root = dirname(__DIR__, 2);
        $js = (string) file_get_contents($root.'/public/assets/ezs-infrastructure.js');

        self::assertStringContainsString('$buttons.removeAttr(\'title\').prop(\'disabled\', true)', $js);
        self::assertStringContainsString("controls[group].start.text('État inconnu')", $js);
        self::assertStringContainsString('if (groupPending[group] || groupActing[group]) return;', $js);
        self::assertStringContainsString("state.state === 'RUNNING' && state.restart === true", $js);
        self::assertStringContainsString("state.state === 'STOPPED' && state.start === true", $js);
        self::assertStringContainsString('$start.prop(\'disabled\',mode === null)', $js);
        self::assertStringContainsString('$stop.prop(\'disabled\',next.stop !== true)', $js);
        self::assertStringContainsString('$cardFor(group).attr(\'data-ezs-probe\',\'unavailable\')', $js);
        self::assertStringContainsString("failGroup(group,'réponse invalide')", $js);
        self::assertStringNotContainsString("dev-groups/'+group+'/restart", $js);
    }
}
