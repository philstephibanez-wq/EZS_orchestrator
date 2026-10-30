<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class DevGroupContextUi051Test extends TestCase
{
    public function testSingleContextualButtonAndVisibleLocalSpinner(): void
    {
        $root = dirname(__DIR__, 2);
        $script = (string) file_get_contents($root.'/public/assets/ezs-infrastructure.js');
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $css = (string) file_get_contents($root.'/public/assets/ezs-debug-layout.css');
        self::assertStringContainsString("state.state === 'RUNNING' && state.restart === true", $script);
        self::assertStringContainsString("state.state === 'STOPPED' && state.start === true", $script);
        self::assertStringContainsString("'Redémarrer'", $script);
        self::assertStringContainsString("action(group,modes[group])", $script);
        self::assertStringContainsString("verb === 'stop' ? controls[group].stop : controls[group].start", $script);
        self::assertStringContainsString('btn-outline-danger', $script);
        self::assertStringContainsString('ezs-debug-rotate', $css);
        self::assertStringContainsString('orchestrator_version|url_encode', $layout);
    }
}
