<?php
declare(strict_types=1);

require dirname(__DIR__) . '/vendor/autoload.php';
use Ezs\Web\Module\Coordination\AssistantAiSupervisorCommand as Supervisor;

if (trim((string) file_get_contents(dirname(__DIR__) . '/VERSION')) !== '4.2c15') {
    throw new RuntimeException('VERSION');
}
$args = Supervisor::arguments('C:/example/llama-server.exe', 'C:/example/model.gguf');
$joined = implode(' ', $args);
foreach (['--host 127.0.0.1', '--port 8720', '--ctx-size 4096', '--parallel 1', '--gpu-layers 0'] as $needle) {
    if (!str_contains($joined, $needle)) {
        throw new RuntimeException('MISSING_ARGUMENT:' . $needle);
    }
}
if ($args[0] !== 'C:/example/llama-server.exe' || $args[2] !== 'C:/example/model.gguf') {
    throw new RuntimeException('MUTATED_PATH');
}
echo "EZS_ASSISTANT_AI_SUPERVISOR_4_2C15_OK\n";
