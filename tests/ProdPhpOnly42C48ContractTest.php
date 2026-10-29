<?php
declare(strict_types=1);

$root = dirname(__DIR__);
foreach (['start.ps1', 'stop.ps1'] as $file) {
    $source = file_get_contents($root . '/scripts/' . $file);
    if (!is_string($source)) {
        throw new RuntimeException('UNREADABLE_SCRIPT ' . $file);
    }
    $start = strpos($source, 'function Invoke-EzsProdLifecycle {');
    if ($start === false) {
        throw new RuntimeException('PROD_HELPER_MISSING ' . $file);
    }
    // The lifecycle is followed by the script entry-point; use its
    // exact terminal marker instead of fragile whitespace delimiters.
    $endMarker = "EZS_PROD_STOP_OWNED_OK";
    $end = strpos($source, $endMarker, $start);
    if ($end === false) {
        throw new RuntimeException('PROD_HELPER_UNTERMINATED ' . $file);
    }
    $section = substr($source, $start, $end - $start + strlen($endMarker));
    foreach ([
        'prod_gateway_php\\router.php',
        'Caddyfile.gateway-php-prod',
        '18515',
        'ezs.prod.php.v1',
        'EZS_PROD_START_MAINTENANCE_OK',
        "name='gateway_php_pid'",
        "name='gateway_pid'",
    ] as $token) {
        if (!str_contains($section, $token)) {
            throw new RuntimeException('MISSING ' . $token . ' ' . $file);
        }
    }
    foreach (['python.exe', 'server.py', 'prod_gateway\\server.py'] as $forbidden) {
        if (str_contains($section, $forbidden)) {
            throw new RuntimeException('LEGACY_PYTHON ' . $file);
        }
    }
}
echo "EZS_PROD_PHP_ONLY_4_2C48_OK\n";
