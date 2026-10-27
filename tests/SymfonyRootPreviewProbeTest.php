<?php
declare(strict_types=1);

/**
 * Sonde HTTP de recette, en lecture seule.
 * Refuse un ancien serveur ou une page portant simplement le nom Orchestrator.
 * Ne démarre, n'arrête ni n'adopte aucun processus.
 */
$host = 'http://127.0.0.1:8890';
$socket = @stream_socket_client('tcp://127.0.0.1:8890', $errno, $errstr, 0.4, STREAM_CLIENT_CONNECT);
if (!is_resource($socket)) {
    fwrite(STDERR, "ROOT_PREVIEW_NOT_RUNNING (8890); aucun processus démarré\n");
    exit(2);
}
fclose($socket);

function readRootPreview(string $host, string $path, int $expectedStatus, string $expectedType): string
{
    $context = stream_context_create(['http' => [
        'timeout' => 3,
        'ignore_errors' => true,
        'follow_location' => 0,
        'header' => "Accept: */*\r\nConnection: close\r\n",
    ]]);
    $body = @file_get_contents($host . $path, false, $context);
    $headers = $http_response_header ?? [];
    $status = $headers[0] ?? '';
    $headerText = implode("\n", $headers);
    $typePattern = $expectedType === 'javascript'
        ? '~^content-type:\\s*(?:text|application)/javascript(?:\\s*;|\\s*$)~im'
        : '~^content-type:\\s*' . preg_quote($expectedType, '~') . '(?:\\s*;|\\s*$)~im';
    if (!preg_match('~^HTTP/\\d(?:\\.\\d)? ' . $expectedStatus . '(?:\\s|$)~', $status)
        || !preg_match($typePattern, $headerText)
        || !is_string($body)) {
        $actualType = 'absent';
        if (preg_match('~^content-type:\\s*([^\\r\\n]+)~im', $headerText, $matches)) {
            $actualType = trim($matches[1]);
        }
        throw new RuntimeException('ROOT_PREVIEW_HTTP_FAILED:' . $path . ' status=' . $status . ' content_type=' . $actualType);
    }
    return $body;
}

$home = readRootPreview($host, '/', 200, 'text/html');
if (!str_contains($home, 'EZS Orchestrator')
    || !str_contains($home, 'ezs-performance-panel')
    || !str_contains($home, 'DEV · EZScore')
    || !str_contains($home, 'PROD · EZScore')
    || !str_contains($home, 'LAB · EZStudio')
    || !str_contains($home, 'Assistant')) {
    throw new RuntimeException('ROOT_PREVIEW_HOME_NOT_FOUR_CARDS');
}
$status = json_decode(readRootPreview($host, '/api/status', 200, 'application/json'), true, 512, JSON_THROW_ON_ERROR);
if (($status['source'] ?? null) !== 'symfony_root'
    || ($status['schema'] ?? null) !== 'ezs.orchestrator.v2.readonly.v1'
    || ($status['migration'] ?? null) !== 'in_progress') {
    throw new RuntimeException('ROOT_PREVIEW_IDENTITY_MISMATCH');
}
$jobs = json_decode(readRootPreview($host, '/api/jobs', 503, 'application/json'), true, 512, JSON_THROW_ON_ERROR);
if (($jobs['error'] ?? null) !== 'jobs_migration_pending'
    || ($jobs['ok'] ?? null) !== false) {
    throw new RuntimeException('ROOT_PREVIEW_JOBS_GATE_MISMATCH');
}
$css = readRootPreview($host, '/assets/ezs-infrastructure.css', 200, 'text/css');
if (!str_contains($css, 'EZS Orchestrator: Bootstrap 5')) {
    throw new RuntimeException('ROOT_PREVIEW_CSS_ASSET_MISMATCH');
}
$js = readRootPreview($host, '/assets/ezs-gpu-monitor.js', 200, 'javascript');
if (!str_contains($js, 'ezsGpuMonitorBooted')) {
    throw new RuntimeException('ROOT_PREVIEW_GPU_JS_ASSET_MISMATCH');
}
echo "SYMFONY_ROOT_PREVIEW_HTTP_OK\n";
