<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class SharedDebugAsync046Test extends TestCase
{
    public function testAsyncCollectionProducesCopiableJsonWithoutTables(): void
    {
        $root = dirname(__DIR__, 2);
        $layout = (string) file_get_contents($root.'/templates/layout/base.html.twig');
        $script = (string) file_get_contents($root.'/public/assets/ezs-dev-debug.js');
        self::assertStringContainsString('Diagnostic non initialisé', $layout);
        self::assertStringContainsString('Collecte en cours', $script);
        self::assertStringContainsString('requests_and_responses:captures', $script);
        self::assertStringContainsString('JSON.stringify(snapshot,null,2)', $script);
        self::assertStringContainsString('navigator.clipboard.writeText(value)', $script);
        self::assertStringContainsString('output.textContent', $script);
        self::assertStringNotContainsString('rows.replaceChildren(newRows)', $script);
        self::assertStringContainsString("window.jQuery(document).ajaxSend", $script);
        self::assertStringContainsString("window.jQuery(document).ajaxComplete", $script);
        self::assertStringContainsString("request:{method:'POST'", $script);
        self::assertStringContainsString("method:'GET'", $script);
        self::assertStringNotContainsString("fetch(url, {method:'POST'", $script);
    }
}
