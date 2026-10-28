<?php
declare(strict_types=1);
$root = dirname(__DIR__);
if (trim((string) file_get_contents($root . '/VERSION')) !== '4.2c12') {
    throw new RuntimeException('VERSION');
}
$client = (string) file_get_contents($root . '/src/Module/Coordination/LabQueueProbe.php');
$caddy = (string) file_get_contents($root . '/config/caddy/Caddyfile.dev-lab-assistant-candidate');
if (!str_contains($client, 'http://127.0.0.1:8702/internal/analysis/desktop/jobs/queue')) {
    throw new RuntimeException('LAB_HTTP_FACADE_REQUIRED');
}
if (str_contains($client, 'http://127.0.0.1:8701/')) {
    throw new RuntimeException('FASTCGI_USED_AS_HTTP');
}
if (!str_contains($caddy, 'http://127.0.0.1:8702') || !str_contains($caddy, 'php_fastcgi 127.0.0.1:8701')) {
    throw new RuntimeException('CADDY_CONTRACT_MISMATCH');
}
echo "EZS_LAB_HTTP_FACADE_4_2C12_OK\n";
