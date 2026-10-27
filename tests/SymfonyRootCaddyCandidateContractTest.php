<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$active = (string) file_get_contents($root . '/config/caddy/Caddyfile.dev');
$candidate = (string) file_get_contents($root . '/config/caddy/Caddyfile.dev-root-candidate');
if ($active === '' || $candidate === '') {
    throw new RuntimeException('CADDY_CANDIDATE_MISSING');
}
$prefix = "# Single isolated Caddy DEV instance: existing Orchestrator plus EZScore sandbox.";
$replacement = "# CANDIDATE V2 ROOT, NOT ACTIVE: validate against current DEV before controlled switch.\n# EZScore sites are identical to the active Caddyfile.dev.";
// Git peut extraire les Caddyfiles en CRLF sous Windows. Comparer la semantique
// exacte apres normalisation des seules fins de ligne, sans ignorer d'autres ecarts.
$normalizeEol = static fn (string $value): string => str_replace(["\r\n", "\r"], "\n", $value);
$expected = str_replace([$prefix, 'root * H:/EZS_orchestrator/web/public'], [$replacement, 'root * H:/EZS_orchestrator/public'], $normalizeEol($active));
$candidate = $normalizeEol($candidate);
if ($candidate !== $expected) {
    throw new RuntimeException('CADDY_CANDIDATE_CHANGED_OTHER_SITE_OR_SECURITY_SETTING');
}
foreach (['http://127.0.0.1:8790', 'php_fastcgi 127.0.0.1:8791', 'http://127.0.0.1:8502', 'http://127.0.0.1:8852', 'forward_auth 127.0.0.1:8502'] as $marker) {
    if (!str_contains($candidate, $marker)) {
        throw new RuntimeException('CADDY_CANDIDATE_CRITICAL_MARKER_MISSING:' . $marker);
    }
}
echo "SYMFONY_ROOT_CADDY_CANDIDATE_OK\n";
