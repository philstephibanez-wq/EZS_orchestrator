<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\RootHealthController;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Request;

final class RootHealthEndpointContractTest extends TestCase
{
    private function request(string $host = '127.0.0.1', int $port = 8790, string $remote = '127.0.0.1'): Request
    {
        return Request::create('http://'.$host.':'.$port.'/health', 'GET', [], [], [],
            ['REMOTE_ADDR' => $remote]);
    }

    public function testHealthIsExplicitlyScopedToDevLoopbackRoot(): void
    {
        $previous = $_SERVER['APP_ENV'] ?? null;
        try {
            $_SERVER['APP_ENV'] = 'dev';
            $controller = new RootHealthController();
            $good = $controller->health($this->request());
            self::assertSame(200, $good->getStatusCode());
            $data = json_decode((string)$good->getContent(), true, 512, JSON_THROW_ON_ERROR);
            self::assertSame('ezs.root.health.v1', $data['schema']);
            self::assertSame('orchestrator-root', $data['component']);
            self::assertSame('HEALTHY', $data['status']);
            self::assertSame(trim((string)file_get_contents(dirname(__DIR__,2).'/VERSION')), $data['version']);
            self::assertArrayNotHasKey('services', $data);
            self::assertArrayNotHasKey('secrets', $data);
            self::assertContains('no-store', array_map('trim', explode(',', (string) $good->headers->get('Cache-Control'))));
            self::assertSame(403, $controller->health($this->request('127.0.0.1',8501))->getStatusCode());
            self::assertSame(403, $controller->health($this->request('localhost',8790,'192.0.2.5'))->getStatusCode());
            $_SERVER['APP_ENV'] = 'prod';
            self::assertSame(403, $controller->health($this->request())->getStatusCode());
        } finally {
            if ($previous === null) unset($_SERVER['APP_ENV']);
            else $_SERVER['APP_ENV'] = $previous;
        }
    }
}
