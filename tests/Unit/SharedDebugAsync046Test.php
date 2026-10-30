<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class SharedDebugAsync046Test extends TestCase
{
    public function testAsyncStateHasNoMisleadingUserInstructionAndPreservesRows(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringNotContainsString('Ouvrir le volet pour recueillir', $layout);
        self::assertStringContainsString('Diagnostic non initialisé', $layout);
        self::assertStringNotContainsString('Diagnostic en attente d’ouverture.', $layout);
        self::assertStringContainsString('Actualisation du diagnostic…', $script);
        self::assertStringContainsString('dernières valeurs conservées', $script);
        self::assertStringContainsString('DocumentFragment', $script);
        self::assertStringContainsString('rows.replaceChildren(newRows)', $script);
        self::assertStringContainsString('Collecte incomplète', $script);
        self::assertStringContainsString('Diagnostic actualisé', $script);
        self::assertStringContainsString('navigator.clipboard.writeText(report)', $script);
        self::assertSame(0, preg_match('/\bmethod\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)["\']/i', $script));
    }
}
