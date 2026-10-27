<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Gpu;

use Symfony\Component\Process\Process;

final class GpuProbe
{
    public function __construct(private readonly GpuTelemetryParser $parser) {}

    public function read(): array
    {
        $binary = self::binary();
        $process = new Process([$binary, '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit,clocks.sm,pstate', '--format=csv,noheader,nounits']);
        $process->setTimeout(10);
        try {
            $process->mustRun();
        } catch (\Throwable $exception) {
            throw new \RuntimeException('gpu_probe_execution_failed', 0, $exception);
        }
        return [
            'node' => 'MAIN',
            'timestamp_utc' => gmdate('c'),
            'gpu' => $this->parser->parse($process->getOutput()),
        ];
    }
    public static function binary(): string
    {
        $configured = getenv('EZS_NVIDIA_SMI');
        if (is_string($configured) && trim($configured) !== '') {
            if (!is_file($configured)) {
                throw new \RuntimeException('gpu_probe_binary_missing');
            }
            return $configured;
        }
        if (PHP_OS_FAMILY === 'Windows') {
            $windows = getenv('WINDIR') ?: getenv('SystemRoot');
            if ($windows) {
                $candidate = rtrim($windows, '\\/') . '/System32/nvidia-smi.exe';
                if (is_file($candidate)) {
                    return $candidate;
                }
            }
            $programFiles = getenv('ProgramFiles');
            if ($programFiles) {
                $candidate = rtrim($programFiles, '\\/') . '/NVIDIA Corporation/NVSMI/nvidia-smi.exe';
                if (is_file($candidate)) {
                    return $candidate;
                }
            }
        }
        return 'nvidia-smi';
    }
}
