<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\NativeCommandRunner;
use PHPUnit\Framework\TestCase;

final class NativeCommandRunnerFastCgiRemovalContractTest extends TestCase
{
    public function testCgiExecutableIsRejectedBeforeAnyProcessCreation(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('NATIVE_COMMAND_NOT_ALLOWED');
        (new NativeCommandRunner())->run('H:/PHP/php-8.5-x64/php-cgi.exe', ['-b', '127.0.0.1:8791'], sys_get_temp_dir());
    }

    public function testCaseInsensitiveExecutableRefusal(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('NATIVE_COMMAND_NOT_ALLOWED');
        (new NativeCommandRunner())->run('H:/PHP/php-8.5-x64/PHP-CGI.EXE', ['-b', '127.0.0.1:8791'], sys_get_temp_dir());
    }

    public function testSourceDoesNotAllowLegacyExecutable(): void
    {
        $source = (string)file_get_contents(dirname(__DIR__, 2).'/src/Module/Infrastructure/NativeCommandRunner.php');
        self::assertStringNotContainsString("'php-cgi.exe' => true", $source);
        self::assertStringContainsString("'php.exe' => true", $source);
    }
}
