<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure;

use Symfony\Component\Process\Process;

/** Canonical FrankenPHP lifecycle boundary. No PHP-CGI or Caddy legacy commands. */
final class NativeSiteLifecycle
{
    private const ROOT = 'H:/EZS_orchestrator';
    private const SCRIPT = self::ROOT.'/scripts/ezs_platform_control.ps1';
    private const SITES = ['dev', 'lab', 'prod'];

    /** @var \Closure(list<string>):array{exit_code:int,stdout:string,stderr:string} */
    private readonly \Closure $invoke;

    public function __construct(?callable $invoke = null)
    {
        $this->invoke = $invoke === null
            ? self::invokeWindows(...)
            : \Closure::fromCallable($invoke);
    }

    /** @return array{exit_code:int,stdout:string,stderr:string} */
    private static function invokeWindows(array $argv): array
    {
        if (PHP_OS_FAMILY !== 'Windows' || !is_file(self::SCRIPT)) {
            throw new \RuntimeException('EZS_NATIVE_SITE_SCRIPT_UNAVAILABLE');
        }
        $process = new Process($argv, self::ROOT);
        $process->setTimeout(30);
        $process->run();
        return [
            'exit_code' => $process->getExitCode() ?? -1,
            'stdout' => $process->getOutput(),
            'stderr' => $process->getErrorOutput(),
        ];
    }

    /** @return list<string> */
    public static function arguments(string $site, string $action): array
    {
        if (!in_array($site, self::SITES, true) || !in_array($action, ['Status', 'Preflight', 'Start', 'Stop'], true)) {
            throw new \InvalidArgumentException('EZS_NATIVE_SITE_ARGUMENT_REFUSED');
        }
        if ($site === 'prod' && $action === 'Stop') {
            throw new \RuntimeException('EZS_PROD_STOP_PROTECTED');
        }
        return [
            'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
            '-File', self::SCRIPT, '-Site', $site, '-Action', $action,
        ];
    }

    /** Run the published, identity-checking PowerShell adapter. No shell command string. */
    public function request(string $site, string $action): string
    {
        $result = ($this->invoke)(self::arguments($site, $action));
        if (!is_array($result) || !isset($result['exit_code'], $result['stdout'], $result['stderr']) ||
            !is_int($result['exit_code']) || !is_string($result['stdout']) || !is_string($result['stderr'])) {
            throw new \RuntimeException('EZS_NATIVE_SITE_RESULT_INVALID');
        }
        if ($result['exit_code'] !== 0) {
            throw new \RuntimeException('EZS_NATIVE_SITE_ACTION_FAILED_'.$site.'_'.$action.'_CODE_'.$result['exit_code']);
        }
        $marker = 'EZS_PLATFORM_'.strtoupper($site).'_'.strtoupper($action).'_OK';
        if (!str_contains($result['stdout'], $marker)) {
            throw new \RuntimeException('EZS_NATIVE_SITE_UNATTESTED_SUCCESS');
        }
        return $result['stdout'];
    }

    /** Native sites have no implicit STOP/START retry or adoption on ambiguous state. */
    public function start(string $site): array
    {
        $this->request($site, 'Preflight');
        $this->request($site, 'Start');
        return [$site => 'START_REQUESTED'];
    }

    public function stop(string $site): array
    {
        $this->request($site, 'Stop');
        return [$site => 'STOP_REQUESTED'];
    }
}
