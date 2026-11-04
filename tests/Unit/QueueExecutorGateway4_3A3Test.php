<?php

declare(strict_types=1);

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\QueueExecutorAccess;
use Ezs\Web\Module\Coordination\QueueExecutorProtocol;
use Ezs\Web\Module\Coordination\Controller\QueueExecutorController;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Request;

final class QueueExecutorGateway4_3A3Test extends TestCase
{
    public function testDisabledByDefaultAndRejectsProducerCredentials(): void
    {
        $beforeFlag = getenv('EZS_QUEUE_EXECUTOR_API');
        $beforeToken = getenv('EZS_QUEUE_EXECUTOR_TOKEN');
        $beforeLab = getenv('EZS_QUEUE_LAB_TOKEN');
        $token = str_repeat('a', 48);
        try {
            putenv('EZS_QUEUE_EXECUTOR_API');
            putenv('EZS_QUEUE_EXECUTOR_TOKEN='.$token);
            self::assertFalse(QueueExecutorAccess::enabled());
            self::assertFalse(QueueExecutorAccess::authorized('Bearer '.$token));
            $controller = new QueueExecutorController();
            $request = Request::create('/api/v2/queue/executor/claim', 'POST', [], [], [], [
                'REMOTE_ADDR' => '127.0.0.1',
                'HTTP_AUTHORIZATION' => 'Bearer '.$token,
                'CONTENT_TYPE' => 'application/json',
            ], '{"resource_class":"gpu","lease_seconds":120}');
            self::assertSame(404, $controller->claim($request)->getStatusCode());
            putenv('EZS_QUEUE_EXECUTOR_API=1');
            putenv('EZS_QUEUE_LAB_TOKEN='.$token);
            self::assertFalse(QueueExecutorAccess::authorized('Bearer '.$token));
            putenv('EZS_QUEUE_LAB_TOKEN='.str_repeat('b', 48));
            self::assertTrue(QueueExecutorAccess::authorized('Bearer '.$token));
            self::assertFalse(QueueExecutorAccess::authorized('Bearer '.str_repeat('c', 48)));
            self::assertSame(403, $controller->claim(Request::create(
                '/api/v2/queue/executor/claim', 'POST', [], [], [], [
                    'REMOTE_ADDR' => '203.0.113.1',
                    'HTTP_AUTHORIZATION' => 'Bearer '.$token,
                ], '{}'
            ))->getStatusCode());
        } finally {
            self::restore('EZS_QUEUE_EXECUTOR_API', $beforeFlag);
            self::restore('EZS_QUEUE_EXECUTOR_TOKEN', $beforeToken);
            self::restore('EZS_QUEUE_LAB_TOKEN', $beforeLab);
        }
    }

    public function testStrictTechnicalFields(): void
    {
        $input = ['resource_class' => 'gpu', 'lease_seconds' => 120];
        self::assertSame($input, QueueExecutorProtocol::claimInput($input));
        foreach ([['audio_path' => 'private.wav'], ['lease_seconds' => '120'], ['resource_class' => 'both']] as $invalid) {
            try {
                QueueExecutorProtocol::claimInput(array_replace($input, $invalid));
                self::fail('Bad claim accepted');
            } catch (\InvalidArgumentException) {
                self::assertTrue(true);
            }
        }
        $beat = [
            'job_id' => 12,
            'claim_generation' => 1,
            'lease_token' => str_repeat('a', 64),
            'lease_seconds' => 120,
            'progress_percent' => null,
        ];
        self::assertSame($beat, QueueExecutorProtocol::heartbeatInput($beat));
        foreach ([['claim_generation' => 0], ['progress_percent' => 100], ['lease_token' => 'invalid'], ['message' => 'secret']] as $invalid) {
            try {
                QueueExecutorProtocol::heartbeatInput(array_replace($beat, $invalid));
                self::fail('Bad heartbeat accepted');
            } catch (\InvalidArgumentException) {
                self::assertTrue(true);
            }
        }
    }

    public function testExclusiveGpuLeaseAndFencedHeartbeatOnTemporarySqlite(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite required');
        }
        $tempRoot = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        self::assertDirectoryExists($tempRoot);
        $path = tempnam($tempRoot, 'ezs-exec-');
        self::assertIsString($path);
        try {
            $queue = new GlobalQueueStore($path);
            $queue->enqueue('lab', 'analysis_job:901', 'lab.analysis_job.901', 'profile', 'gpu', 50);
            $queue->enqueue('lab', 'analysis_job:902', 'lab.analysis_job.902', 'profile', 'gpu', 50);
            $first = QueueExecutorProtocol::claim($queue, QueueExecutorProtocol::claimInput([
                'resource_class' => 'gpu', 'lease_seconds' => 120,
            ]));
            self::assertIsArray($first);
            self::assertSame('running', $queue->byId($first['id'])['state']);
            self::assertArrayHasKey('lease_token', $first);
            self::assertArrayNotHasKey('idempotency_key', $first);
            self::assertNull(QueueExecutorProtocol::claim($queue, ['resource_class' => 'gpu', 'lease_seconds' => 120]));
            $heartbeat = QueueExecutorProtocol::heartbeat($queue, QueueExecutorProtocol::heartbeatInput([
                'job_id' => $first['id'],
                'claim_generation' => $first['claim_generation'],
                'lease_token' => $first['lease_token'],
                'lease_seconds' => 120,
                'progress_percent' => 20,
            ]));
            self::assertSame(20, $heartbeat['progress_percent']);
            try {
                QueueExecutorProtocol::heartbeat($queue, [
                    'job_id' => $first['id'], 'claim_generation' => $first['claim_generation'] + 1,
                    'lease_token' => $first['lease_token'], 'lease_seconds' => 120, 'progress_percent' => 30,
                ]);
                self::fail('Stale generation accepted');
            } catch (\DomainException) {
                self::assertTrue(true);
            }
            try {
                QueueExecutorProtocol::heartbeat($queue, [
                    'job_id' => $first['id'], 'claim_generation' => $first['claim_generation'],
                    'lease_token' => str_repeat('f', 64), 'lease_seconds' => 120, 'progress_percent' => 30,
                ]);
                self::fail('Wrong lease accepted');
            } catch (\DomainException) {
                self::assertTrue(true);
            }
            self::assertSame('queued', $queue->byId($first['id'] + 1)['state']);
        } finally {
            unset($queue);
            foreach ([$path, $path.'-wal', $path.'-shm'] as $file) {
                if (is_file($file)) @unlink($file);
            }
        }
    }

    private static function restore(string $key, string|false $value): void
    {
        if ($value === false) {
            putenv($key);
        } else {
            putenv($key.'='.$value);
        }
    }
}
