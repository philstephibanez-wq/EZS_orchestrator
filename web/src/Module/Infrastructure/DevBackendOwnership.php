<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

final class DevBackendOwnership
{
    public function snapshot(): array
    {
        $port = 8602;
        $socket = @stream_socket_client('tcp://127.0.0.1:' . $port, $errno, $error, 0.3, STREAM_CLIENT_CONNECT);
        $tcp = is_resource($socket);
        if ($tcp) fclose($socket);
        if (!$tcp) return ['port'=>$port, 'tcp_listening'=>false, 'ownership'=>'absent', 'pid'=>null];
        if (PHP_OS_FAMILY !== 'Windows') return ['port'=>$port, 'tcp_listening'=>true, 'ownership'=>'unknown', 'pid'=>null];
        try {
            $command = ['powershell.exe','-NoProfile','-NonInteractive','-Command',
                '(Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8602 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess'];
            $descriptor = [0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']];
            $process = @proc_open($command,$descriptor,$pipes,null,null,['bypass_shell'=>true]);
            if (!is_resource($process)) return ['port'=>$port,'tcp_listening'=>true,'ownership'=>'unknown','pid'=>null];
            fclose($pipes[0]);
            $output = trim((string)stream_get_contents($pipes[1]));
            fclose($pipes[1]);fclose($pipes[2]);proc_close($process);
            $pid = ctype_digit($output) ? (int)$output : 0;
            if ($pid < 1) return ['port'=>$port,'tcp_listening'=>true,'ownership'=>'unknown','pid'=>null];
            // Reading the owning PID is not proof of identity; don't report "owned".
            return ['port'=>$port,'tcp_listening'=>true,'ownership'=>'unverified','pid'=>$pid];
        } catch (\Throwable) {
            return ['port'=>$port,'tcp_listening'=>true,'ownership'=>'unknown','pid'=>null];
        }
    }
}
