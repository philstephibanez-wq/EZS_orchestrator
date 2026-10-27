<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure;

use Symfony\Component\Process\Exception\ProcessFailedException;
use Symfony\Component\Process\Process;

/**
 * V2 system boundary. No shell scripts or interpreter wrappers.
 * Running this class does not alone certify zero visible windows on Windows 11;
 * this is a separate mandatory live acceptance gate.
 */
final class NativeCommandRunner
{
    private const ALLOWED = [
        'git.exe' => true,
        'caddy.exe' => true,
        'php.exe' => true,
        'php-cgi.exe' => true,
        'nvidia-smi.exe' => true,
    ];

    /** @param list<string> $arguments
     *  @return array{exit_code:int,stdout:string,stderr:string}
     */
    public function run(string $executable, array $arguments, string $cwd, float $timeout = 15.0): array
    {
        if ($executable === '' || !is_dir($cwd) || $timeout <= 0 || $timeout > 300) {
            throw new \InvalidArgumentException('NATIVE_COMMAND_INVALID');
        }
        $name = strtolower(basename(str_replace('\\', '/', $executable)));
        if (!isset(self::ALLOWED[$name]) || strpbrk($executable, "\r\n\0") !== false) {
            throw new \InvalidArgumentException('NATIVE_COMMAND_NOT_ALLOWED');
        }
        foreach ($arguments as $arg) {
            if (!is_string($arg) || strpbrk($arg, "\r\n\0") !== false) {
                throw new \InvalidArgumentException('NATIVE_ARGUMENT_INVALID');
            }
        }
        // Symfony Process receives an argv array, never a shell command string.
        $process = new Process(array_merge([$executable], $arguments), $cwd);
        $process->setTimeout($timeout);
        $process->run();
        return [
            'exit_code' => $process->getExitCode() ?? -1,
            'stdout' => $process->getOutput(),
            'stderr' => $process->getErrorOutput(),
        ];
    }
}
