<?php
declare(strict_types=1);

$root = dirname(__DIR__);
require_once $root . '/src/Module/Gpu/GpuTelemetryParser.php';
require_once $root . '/src/Module/Gpu/GpuProbe.php';

$parser = new \Ezs\Web\Module\Gpu\GpuTelemetryParser();
$gpu = $parser->parse('NVIDIA GeForce RTX 2060, 0, 0, 6144, 55, 29.85, [N/A], 960, P0');
if ($gpu['name'] !== 'NVIDIA GeForce RTX 2060'
    || $gpu['memory_total_mib'] !== 6144.0
    || $gpu['temperature_c'] !== 55.0
    || $gpu['power_w'] !== 29.85
    || $gpu['power_limit_w'] !== null
    || $gpu['sm_clock_mhz'] !== 960.0
    || $gpu['pstate'] !== 'P0') {
    throw new \RuntimeException('GPU_MAIN_CSV_PARSE_FAILED');
}
$previous = getenv('EZS_NVIDIA_SMI');
putenv('EZS_NVIDIA_SMI=' . $root . '/absent-nvidia-smi.exe');
try {
    \Ezs\Web\Module\Gpu\GpuProbe::binary();
    throw new \RuntimeException('INVALID_GPU_OVERRIDE_ACCEPTED');
} catch (\RuntimeException $e) {
    if ($e->getMessage() !== 'gpu_probe_binary_missing') {
        throw $e;
    }
} finally {
    $previous === false ? putenv('EZS_NVIDIA_SMI') : putenv('EZS_NVIDIA_SMI=' . $previous);
}
echo "GPU_MAIN_CSV_CONTRACT_OK\n";
