<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugLayout044Test extends TestCase
{
    public function testPanelUsesSharedSidebarOffsetAndScrollableReport(): void
    {
        $root = dirname(__DIR__, 2);
        $twig = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $css = (string) file_get_contents($root.'/public/assets/ezs-debug-layout.css');
        self::assertStringContainsString('class="container-fluid pb-3 ezs-debug-region"', $twig);
        self::assertStringContainsString('ezs-debug-report', $twig);
        self::assertStringContainsString('width: calc(100% - var(--ezs-perf-width))', $css);
        self::assertStringContainsString('margin-left: var(--ezs-perf-width)', $css);
        self::assertStringContainsString('overflow: auto', $css);
        self::assertStringContainsString('@media (max-width: 1000px)', $css);
        self::assertStringContainsString('id="ezs-debug-copy"', $twig);
        self::assertStringContainsString('app.request.port == 8790', $twig);
    }
}
