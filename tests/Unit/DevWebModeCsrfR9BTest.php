<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class DevWebModeCsrfR9BTest extends TestCase
{
    public function testCsrfDoesNotDependOnPhpSessionAndIsNotPublishedUnderDocumentRoot(): void
    {
        $src = (string) file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/Controller/DevWebModeController.php');
        self::assertStringNotContainsString('session_start(', $src);
        self::assertStringNotContainsString('$_SESSION', $src);
        self::assertStringContainsString('dev-csrf.key', $src);
        self::assertStringContainsString('random_bytes(32)', $src);
        self::assertStringContainsString('flock($handle, LOCK_EX)', $src);
        self::assertStringContainsString("'X-EZS-CSRF'", $src);
        self::assertStringContainsString('hash_equals($csrf', $src);
        self::assertStringContainsString('invalid_origin', $src);
    }
}
