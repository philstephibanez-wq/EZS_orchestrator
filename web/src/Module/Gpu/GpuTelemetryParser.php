<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Gpu;

final class GpuTelemetryParser
{
    public function parse(string $output): array
    {
        $line = trim(explode("\n", trim($output))[0] ?? '');
        $fields = str_getcsv($line);
        if (count($fields) !== 5) {
            throw new \UnexpectedValueException('gpu_invalid_field_count');
        }
        [$name, $usage, $used, $total, $temperature] = array_map('trim', $fields);
        if ($name === '' || !is_numeric($usage) || !is_numeric($used) || !is_numeric($total) || !is_numeric($temperature) || (float)$total <= 0) {
            throw new \UnexpectedValueException('gpu_invalid_measurements');
        }
        return [
            'name' => $name,
            'utilization_percent' => (float)$usage,
            'memory_used_mib' => (float)$used,
            'memory_total_mib' => (float)$total,
            'temperature_c' => (float)$temperature,
        ];
    }
}
