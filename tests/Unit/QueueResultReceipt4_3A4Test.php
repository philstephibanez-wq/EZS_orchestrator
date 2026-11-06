<?php

declare(strict_types=1);

use Ezs\Web\Module\Coordination\Controller\QueueExecutorFinishController;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\QueueResultReceipt;
use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpFoundation\Request;

final class QueueResultReceipt4_3A4Test extends TestCase
{
    private const SECRET = 'fixture-only-result-attestation-secret-44-chars';

    private static function envelope(int $jobId = 7, int $generation = 2, string $result = 'completed'): array
    {
        $receipt = [
            'schema' => 'ezs.lab.persisted-result.v1',
            'producer' => 'lab',
            'external_id' => 'analysis_job:201',
            'job_id' => $jobId,
            'claim_generation' => $generation,
            'result' => $result,
            'artifact_sha256' => $result === 'completed' ? str_repeat('a', 64) : null,
            'signature' => str_repeat('0', 64),
        ];
        $receipt['signature'] = hash_hmac('sha256', QueueResultReceipt::canonical($receipt), self::SECRET);
        return [
            'job_id' => $jobId,
            'claim_generation' => $generation,
            'lease_token' => str_repeat('f', 64),
            'receipt' => $receipt,
        ];
    }

    public function testExactReceiptAndCryptographicBinding(): void
    {
        $data = self::envelope();
        $current = ['id' => 7, 'claim_generation' => 2, 'producer' => 'lab', 'external_id' => 'analysis_job:201'];
        self::assertSame($data, QueueResultReceipt::parse($data));
        self::assertTrue(QueueResultReceipt::verify($data, $current, self::SECRET));
        self::assertFalse(QueueResultReceipt::verify($data, $current, str_repeat('x', 48)));
        self::assertFalse(QueueResultReceipt::verify($data, array_replace($current, ['claim_generation' => 3]), self::SECRET));
        self::assertFalse(QueueResultReceipt::verify($data, array_replace($current, ['producer' => 'dev']), self::SECRET));
        self::assertFalse(QueueResultReceipt::verify($data, array_replace($current, ['external_id' => 'analysis_job:202']), self::SECRET));
        $bad = $data;
        $bad['receipt']['artifact_sha256'] = str_repeat('b', 64);
        self::assertFalse(QueueResultReceipt::verify($bad, $current, self::SECRET));
    }

    public function testMalformedAndUnattestedResultsFailClosed(): void
    {
        foreach ([
            ['receipt' => ['signature' => 'bad']],
            ['receipt' => ['schema' => 'unknown']],
            ['receipt' => ['result' => 'running']],
            ['receipt' => ['artifact_sha256' => null]],
            ['receipt' => ['external_id' => 'analysis_job:0']],
            ['claim_generation' => '2'],
            ['song_title' => 'secret'],
        ] as $invalid) {
            $data = self::envelope();
            foreach ($invalid as $field => $value) {
                if ($field === 'receipt') {
                    $data['receipt'] = array_replace($data['receipt'], $value);
                } else {
                    $data[$field] = $value;
                }
            }
            try {
                QueueResultReceipt::parse($data);
                self::fail('Invalid receipt accepted');
            } catch (\InvalidArgumentException) {
                self::assertTrue(true);
            }
        }
        $failed = self::envelope(7, 2, 'failed');
        self::assertSame($failed, QueueResultReceipt::parse($failed));
    }

    public function testDisabledHttpDoesNotOpenQueue(): void
    {
        $before = getenv('EZS_QUEUE_EXECUTOR_API');
        try {
            putenv('EZS_QUEUE_EXECUTOR_API=0');
            $request = Request::create('/api/v2/queue/executor/finish', 'POST', [], [], [], [
                'REMOTE_ADDR' => '127.0.0.1',
                'CONTENT_TYPE' => 'application/json',
            ], '{}');
            $response = (new QueueExecutorFinishController())->finish($request);
            self::assertSame(404, $response->getStatusCode());
            self::assertStringContainsString('executor_api_disabled', (string) $response->getContent());
        } finally {
            $before === false ? putenv('EZS_QUEUE_EXECUTOR_API') : putenv('EZS_QUEUE_EXECUTOR_API='.$before);
        }
    }

    public function testSyntheticQueueCannotCompleteWithoutMatchingReceipt(): void
    {
        if (!extension_loaded('pdo_sqlite')) {
            self::markTestSkipped('pdo_sqlite required');
        }
        $root = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        self::assertDirectoryExists($root);
        $path = tempnam($root, 'ezs-finish-');
        self::assertIsString($path);
        try {
            $store = new GlobalQueueStore($path);
            $store->enqueue('lab', 'analysis_job:201', 'lab.analysis_job.201', 'profile', 'gpu');
            $claimed = $store->claim('gpu', 120);
            self::assertIsArray($claimed);
            $data = self::envelope((int) $claimed['id'], (int) $claimed['claim_generation']);
            self::assertTrue(QueueResultReceipt::verify($data, $claimed, self::SECRET));
            $tampered = $data;
            $tampered['receipt']['result'] = 'failed';
            $tampered['receipt']['artifact_sha256'] = null; // Valid failure shape; stale signature must fail.
            self::assertSame($tampered, QueueResultReceipt::parse($tampered));
            self::assertFalse(QueueResultReceipt::verify($tampered, $claimed, self::SECRET));
            self::assertSame('running', $store->byId((int) $claimed['id'])['state']);
            $store->finish((int) $claimed['id'], (string) $claimed['lease_token'], true);
            self::assertSame('completed', $store->byId((int) $claimed['id'])['state']);
        } finally {
            unset($store);
            foreach ([$path, $path.'-wal', $path.'-shm'] as $file) {
                if (is_file($file)) {
                    @unlink($file);
                }
            }
        }
    }
}
