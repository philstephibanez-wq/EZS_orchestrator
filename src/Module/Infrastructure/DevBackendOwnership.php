<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

/** Strict identity classification. Does not adopt or terminate a process. */
final class DevBackendOwnership
{
    private const PORT = 8602;
    private const ROOT = 'H:\\EZScore_dev\\public';
    private const PHP_EXE = 'H:\\PHP\\php-8.5-x64\\php.exe';

    public static function classify(int $listenerPid, array $process): string
    {
        if ($listenerPid <= 0) return 'unknown';
        if ((int)($process['ProcessId'] ?? 0) !== $listenerPid) return 'foreign';
        $exe = str_replace('/', '\\', trim((string)($process['ExecutablePath'] ?? ''), '"'));
        if (strcasecmp($exe, self::PHP_EXE) !== 0) return 'foreign';
        $line = str_replace('/', '\\', (string)($process['CommandLine'] ?? ''));
        // Match exact arguments, avoiding false positives such as port 86020 or suffixes.
        $port = preg_match('/(?:^|\\s)-S\\s+127\\.0\\.0\\.1:8602(?=\\s|$)/i', $line) === 1;
        $root = preg_match('~(?:^|\\s)-t\\s+["\\x27]?' . preg_quote(self::ROOT, '~') . '["\\x27]?(?=\\s|$)~i', $line) === 1;
        return $port && $root ? 'legacy_exact' : 'foreign';
    }

    public function snapshot(): array
    {
        $result = ['port'=>self::PORT,'tcp_listening'=>false,'ownership'=>'absent','pid'=>null];
        $socket = @stream_socket_client('tcp://127.0.0.1:8602', $errno, $error, 0.3, STREAM_CLIENT_CONNECT);
        if (!is_resource($socket)) return $result;
        fclose($socket);
        $result['tcp_listening'] = true;
        $result['ownership'] = 'unknown';
        if (PHP_OS_FAMILY !== 'Windows') return $result;
        $code = <<<'PS'
$listener = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8602 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $listener) { exit 2 }
$owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
if (-not $owner) { exit 3 }
[pscustomobject]@{ ProcessId=[int]$owner.ProcessId; ExecutablePath=[string]$owner.ExecutablePath; CommandLine=[string]$owner.CommandLine } | ConvertTo-Json -Compress
PS;
        $cmd = ['powershell.exe','-NoProfile','-NonInteractive','-Command',$code];
        try {
            $proc = @proc_open($cmd,[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,null,null,['bypass_shell'=>true]);
            if (!is_resource($proc)) return $result;
            fclose($pipes[0]);
            $raw = stream_get_contents($pipes[1], 8192);
            fclose($pipes[1]);
            fclose($pipes[2]);
            if (proc_close($proc) !== 0) return $result;
            $data = json_decode((string)$raw, true);
            if (!is_array($data)) return $result;
            $pid = (int)($data['ProcessId'] ?? 0);
            if ($pid <= 0) return $result;
            $result['pid'] = $pid;
            $result['ownership'] = self::classify($pid, $data);
        } catch (\Throwable) { /* Fail closed: unknown owner. */ }
        return $result;
    }
}
