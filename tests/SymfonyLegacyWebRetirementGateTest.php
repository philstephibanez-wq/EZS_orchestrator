<?php
declare(strict_types=1);

/**
 * Gate durable : la disparition de web/ est interdite tant que la bascule
 * HTTP et la parité des API historiques ne sont pas acquises.
 */
$root = dirname(__DIR__);
$ignore = (string) file_get_contents($root . '/.gitignore');
foreach ([
    '/web/vendor/',
    '/web/var/',
    '/web/.env.local',
    '/web/.env.*.local',
    '/web/config/reference.php',
] as $rule) {
    if (!preg_match('/^' . preg_quote($rule, '/') . '$/m', $ignore)) {
        throw new RuntimeException('LEGACY_IGNORE_PROTECTION_MISSING:' . $rule);
    }
}
$legacyIgnore = $root . '/web/.gitignore';
if (!is_file($legacyIgnore)) {
    throw new RuntimeException('LEGACY_WEB_REMOVED_BEFORE_RUNTIME_GATE');
}
foreach ([
    '/vendor/',
    '/var/',
    '/config/reference.php',
] as $rule) {
    if (!preg_match('/^' . preg_quote($rule, '/') . '$/m', (string) file_get_contents($legacyIgnore))) {
        throw new RuntimeException('LEGACY_NESTED_IGNORE_MISSING:' . $rule);
    }
}
$caddy = (string) file_get_contents($root . '/config/caddy/Caddyfile.dev');
if (!str_contains($caddy, 'root * H:/EZS_orchestrator/web/public')) {
    throw new RuntimeException('DEV_CADDY_SWITCH_NOT_CONTRACTUALLY_VALIDATED');
}
$start = (string) file_get_contents($root . '/scripts/start.ps1');
if (!str_contains($start, 'EZS_V2_START_NOT_READY')) {
    throw new RuntimeException('START_GATE_UNEXPECTEDLY_OPENED');
}
$jobs = (string) file_get_contents($root . '/src/Module/Infrastructure/Controller/LegacyReadOnlyController.php');
if (!str_contains($jobs, 'jobs_migration_pending')) {
    throw new RuntimeException('JOBS_GATE_UNEXPECTEDLY_OPENED');
}
echo "SYMFONY_LEGACY_WEB_RETIREMENT_GATE_OK\n";
