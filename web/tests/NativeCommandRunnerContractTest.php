<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/NativeCommandRunner.php';

use Ezs\Web\Module\Infrastructure\NativeCommandRunner;

$runner = new NativeCommandRunner();
foreach ([
    ['powershell.exe', []],
    ['cmd.exe', ['/c', 'echo']],
    ['python.exe', ['--version']],
    ['git.exe', ["status\nmalicious"]],
] as [$binary, $argv]) {
    try {
        $runner->run($binary, $argv, dirname(__DIR__));
        throw new RuntimeException('unexpected_acceptance:'.$binary);
    } catch (InvalidArgumentException $expected) {
        // Forbidden command rejected before execution.
    }
}
echo "NATIVE_COMMAND_BOUNDARY_OK\n";
