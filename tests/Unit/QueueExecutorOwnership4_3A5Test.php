<?php

declare(strict_types=1);

use Ezs\Web\Module\Coordination\Controller\QueueExecutorOwnershipController;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Request;

final class QueueExecutorOwnership4_3A5Test extends TestCase
{
    public function testOwnershipEndpointIsDisabledByDefaultAndRejectsForeignPeers(): void
    {
        $beforeFlag = getenv('EZS_QUEUE_EXECUTOR_API');
        $beforeToken = getenv('EZS_QUEUE_EXECUTOR_TOKEN');
        $beforeProducer = getenv('EZS_QUEUE_LAB_TOKEN');
        $priorServer = $_SERVER['EZS_QUEUE_EXECUTOR_API'] ?? null;
        $priorEnv = $_ENV['EZS_QUEUE_EXECUTOR_API'] ?? null;
        try {
            putenv('EZS_QUEUE_EXECUTOR_API');
            unset($_SERVER['EZS_QUEUE_EXECUTOR_API'], $_ENV['EZS_QUEUE_EXECUTOR_API']);
            $controller = new QueueExecutorOwnershipController();
            self::assertSame(404, $controller->register(Request::create(
                '/api/v2/queue/executor/ownership', 'POST', [], [], [], ['REMOTE_ADDR'=>'127.0.0.1']
            ))->getStatusCode());
            putenv('EZS_QUEUE_EXECUTOR_API=1');
            putenv('EZS_QUEUE_EXECUTOR_TOKEN='.str_repeat('q',48));
            putenv('EZS_QUEUE_LAB_TOKEN='.str_repeat('r',48));
            self::assertSame(403, $controller->register(Request::create(
                '/api/v2/queue/executor/ownership', 'POST', [], [], [], [
                    'REMOTE_ADDR'=>'192.0.2.3', 'HTTP_AUTHORIZATION'=>'Bearer '.str_repeat('q',48),
                ]
            ))->getStatusCode());
            self::assertSame(422, $controller->register(Request::create(
                '/api/v2/queue/executor/ownership', 'POST', [], [], [], [
                    'REMOTE_ADDR'=>'127.0.0.1', 'HTTP_AUTHORIZATION'=>'Bearer '.str_repeat('q',48),
                    'CONTENT_TYPE'=>'application/json',
                ], '{"foo":"bar"}'
            ))->getStatusCode());
        } finally {
            foreach (['EZS_QUEUE_EXECUTOR_API'=>$beforeFlag,'EZS_QUEUE_EXECUTOR_TOKEN'=>$beforeToken,'EZS_QUEUE_LAB_TOKEN'=>$beforeProducer] as $name => $value) {
                if ($value === false) putenv($name);
                else putenv($name.'='.$value);
            }
            if ($priorServer === null) unset($_SERVER['EZS_QUEUE_EXECUTOR_API']);
            else $_SERVER['EZS_QUEUE_EXECUTOR_API'] = $priorServer;
            if ($priorEnv === null) unset($_ENV['EZS_QUEUE_EXECUTOR_API']);
            else $_ENV['EZS_QUEUE_EXECUTOR_API'] = $priorEnv;
        }
    }
}
