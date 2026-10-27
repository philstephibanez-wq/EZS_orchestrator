<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Gpu/GpuTelemetryParser.php';
use Ezs\Web\Module\Gpu\GpuTelemetryParser;

$parser = new GpuTelemetryParser();
$actual = $parser->parse("RTX 2060, 32, 1024, 6144, 58\r\n");
if ($actual['name'] !== 'RTX 2060' || $actual['memory_used_mib'] !== 1024.0 || $actual['temperature_c'] !== 58.0) {
    throw new \RuntimeException('invalid_gpu_parse');
}
try {
    $parser->parse('invalid');
    throw new \RuntimeException('invalid_input_accepted');
} catch (\UnexpectedValueException) {
}
echo "GPU_PARSER_OK\n";
