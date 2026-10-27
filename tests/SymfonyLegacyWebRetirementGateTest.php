<?php
declare(strict_types=1);
$root = dirname(__DIR__);
if (is_dir($root . '/web')) {
    throw new RuntimeException('LEGACY_WEB_DIRECTORY_REMAINS');
}
$caddy = (string) file_get_contents($root . '/config/caddy/Caddyfile.dev');
if (!str_contains($caddy, 'root * H:/EZS_orchestrator/public')
    || str_contains($caddy, 'EZS_orchestrator/web/public')) {
    throw new RuntimeException('CADDY_DEV_NOT_ROOTED');
}
foreach (['src/Kernel.php', 'public/index.php', 'bin/console', 'composer.lock', 'templates/infrastructure/index.html.twig'] as $relative) {
    if (!is_file($root . '/' . $relative)) {
        throw new RuntimeException('ROOT_APP_MISSING:' . $relative);
    }
}
echo "SYMFONY_LEGACY_WEB_RETIREMENT_GATE_OK\n";
