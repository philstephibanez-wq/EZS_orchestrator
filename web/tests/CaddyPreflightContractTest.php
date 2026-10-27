<?php
declare(strict_types=1);

$file = file_get_contents(dirname(__DIR__) . '/config/caddy/Caddyfile.dev-preflight');
if ($file === false) {
    throw new RuntimeException('caddy_preflight_missing');
}
foreach (['127.0.0.1:8790', '127.0.0.1:8791', 'admin off', 'php_fastcgi', 'bind 127.0.0.1'] as $expected) {
    if (!str_contains($file, $expected)) {
        throw new RuntimeException('missing_preflight_contract: ' . $expected);
    }
}
foreach ([':8501', ':8502', ':8701', ':2019', 'reverse_proxy', 'forward_auth'] as $forbidden) {
    if (str_contains($file, $forbidden)) {
        throw new RuntimeException('existing_service_or_prod_overlap: ' . $forbidden);
    }
}
echo "CADDY_PREFLIGHT_CONTRACT_OK\n";
