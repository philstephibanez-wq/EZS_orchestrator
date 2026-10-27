<?php
declare(strict_types=1);

/**
 * Read-only smoke test for manually started isolated root preview.
 * Does not start, stop or adopt any process.
 */
$targets = [
    '/' => ['content' => 'text/html', 'marker' => 'EZS Orchestrator'],
    '/api/v2/environments' => ['content' => 'application/json', 'marker' => 'ezs.environments.v1'],
];
$host = 'http://127.0.0.1:8890';
$socket = @stream_socket_client('tcp://127.0.0.1:8890', $errno, $errstr, 0.4, STREAM_CLIENT_CONNECT);
if (!is_resource($socket)) {
    fwrite(STDERR, "ROOT_PREVIEW_NOT_RUNNING (8890); no process started\n");
    exit(2);
}
fclose($socket);
foreach ($targets as $uri => $expected) {
    $context = stream_context_create(['http' => [
        'timeout' => 3,
        'ignore_errors' => true,
        'follow_location' => 0,
        'header' => "Accept: */*\r\nConnection: close\r\n",
    ]]);
    $body = @file_get_contents($host.$uri, false, $context);
    $headers = $http_response_header ?? [];
    $status = $headers[0] ?? '';
    $headerText = implode("\n", $headers);
    if (!preg_match('~^HTTP/\\d(?:\\.\\d)? 200(?:\\s|$)~', $status)
        || !preg_match('~content-type:\\s*'.preg_quote($expected['content'], '~').'~i', $headerText)
        || !is_string($body)
        || !str_contains($body, $expected['marker'])) {
        throw new RuntimeException('ROOT_PREVIEW_HTTP_FAILED:'.$uri.' status='.$status);
    }
}
echo "SYMFONY_ROOT_PREVIEW_HTTP_OK\n";
