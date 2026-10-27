<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Gpu;

use Symfony\Component\Process\Process;

final class GpuProbe
{
    public function __construct(private readonly GpuTelemetryParser $parser) {}

    public function read(): array
    {
        $binary = getenv('EZS_NVIDIA_SMI') ?: 'nvidia-smi';
        $process = new Process([$binary, '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu', '--format=csv,noheader,nounits']);
        $process->setTimeout(5);
        $process->mustRun();
        return [
            'node' => 'MAIN',
            'timestamp_utc' => gmdate('c'),
            'gpu' => $this->parser->parse($process->getOutput()),
        ];
    }
}
