<?php
declare(strict_types=1);

// In-process HTTP/HTML smoke: no TCP listener, no Caddy launch, no worker execution.
$root = dirname(__DIR__);
$autoload = $root.'/vendor/autoload.php';
if (!is_file($autoload)) {
    fwrite(STDERR, "ROOT_VENDOR_MISSING\n");
    exit(2);
}
require_once $autoload;

use Ezs\Web\Kernel;
use Symfony\Component\HttpFoundation\Request;

$kernel = new Kernel('dev', true);
try {
    $kernel->boot();
    foreach ([
        ['/', 'text/html', [trim((string) file_get_contents($root.'/VERSION'))]],
        ['/api/v2/environments', 'application/json', ['orchestrator']],
    ] as [$uri, $type, $markers]) {
        $request = Request::create($uri, 'GET', [], [], [], [
            'HTTP_HOST' => '127.0.0.1',
            'REMOTE_ADDR' => '127.0.0.1',
        ]);
        $response = $kernel->handle($request);
        try {
            if ($response->getStatusCode() !== 200) {
                throw new RuntimeException('ROOT_HTTP_STATUS_'.$uri.'_'.$response->getStatusCode());
            }
            if (!str_contains((string)$response->headers->get('content-type'), $type)) {
                throw new RuntimeException('ROOT_HTTP_CONTENT_TYPE_'.$uri);
            }
            foreach ($markers as $marker) {
                if (!str_contains((string)$response->getContent(), $marker)) {
                    throw new RuntimeException('ROOT_HTTP_MARKER_MISSING_'.$uri.'_'.$marker);
                }
            }
        } finally {
            $kernel->terminate($request, $response);
        }
    }
    echo "SYMFONY_ROOT_HTTP_KERNEL_OK\n";
} finally {
    $kernel->shutdown();
}
