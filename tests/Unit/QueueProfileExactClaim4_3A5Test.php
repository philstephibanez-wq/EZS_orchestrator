<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\QueueExecutorProtocol;
use PHPUnit\Framework\TestCase;

final class QueueProfileExactClaim4_3A5Test extends TestCase
{
    public function testExactClaimDoesNotConsumeOtherJobs(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite_required');
        $temp = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $file = $temp.'/ezs-profile-claim-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $queue = new GlobalQueueStore($file);
            $first = $queue->enqueue('lab', 'analysis_job:903', 'test.profile.903', 'profile', 'gpu', 60);
            $second = $queue->enqueue('lab', 'analysis_job:904', 'test.profile.904', 'profile', 'gpu', 50);
            $input = QueueExecutorProtocol::claimInput([
                'resource_class'=>'gpu', 'lease_seconds'=>120,
                'job_id'=>(int)$second['id'], 'kind'=>'profile',
            ]);
            $picked = QueueExecutorProtocol::claim($queue, $input);
            self::assertIsArray($picked);
            self::assertSame((int)$second['id'], $picked['id']);
            self::assertSame('queued', $queue->byId((int)$first['id'])['state']);
            self::assertSame('running', $queue->byId((int)$second['id'])['state']);
            self::assertNull(QueueExecutorProtocol::claim($queue, $input));
        } finally {
            foreach ([$file, $file.'-wal', $file.'-shm'] as $path) if (is_file($path)) @unlink($path);
        }
    }

    public function testExactClaimRefusesForeignKindWithoutClaim(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite_required');
        $temp = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $file = $temp.'/ezs-profile-kind-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $queue = new GlobalQueueStore($file);
            $other = $queue->enqueue('lab', 'analysis_job:905', 'test.stems.905', 'stems', 'gpu');
            $input = QueueExecutorProtocol::claimInput([
                'resource_class'=>'gpu', 'lease_seconds'=>120,
                'job_id'=>(int)$other['id'], 'kind'=>'profile',
            ]);
            self::assertNull(QueueExecutorProtocol::claim($queue, $input));
            self::assertSame('queued', $queue->byId((int)$other['id'])['state']);
        } finally {
            foreach ([$file, $file.'-wal', $file.'-shm'] as $path) if (is_file($path)) @unlink($path);
        }
    }

    public function testLegacyClaimEnvelopeRemainsAccepted(): void
    {
        $input = ['resource_class'=>'cpu', 'lease_seconds'=>60];
        self::assertSame($input, QueueExecutorProtocol::claimInput($input));
        $this->expectException(\InvalidArgumentException::class);
        QueueExecutorProtocol::claimInput($input + ['kind'=>'profile']);
    }
}
