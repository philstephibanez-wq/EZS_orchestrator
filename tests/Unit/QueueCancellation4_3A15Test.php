<?php

declare(strict_types=1);

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

final class QueueCancellation4_3A15Test extends TestCase
{
    public function testQueuedCancelIsFinalAndCannotBeClaimed(): void
    {
        $path = sys_get_temp_dir().'/ezs-cancel-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $store = new GlobalQueueStore($path);
            $job = $store->enqueue('lab','analysis_job:9001','test.cancel.9001','profile','gpu');
            $this->assertSame('cancelled', $store->cancelQueued((int)$job['id'], 'lab')['state']);
            $this->assertSame('cancelled', $store->cancelQueued((int)$job['id'], 'lab')['state']);
            $this->assertNull($store->claim('gpu'));
            $this->expectException(\DomainException::class);
            $store->cancelQueued((int)$job['id'], 'assistant');
        } finally {
            unset($store);
            foreach (['','-wal','-shm'] as $suffix) @unlink($path.$suffix);
        }
    }

    public function testRunningCannotBeCancelledWithoutStopAttestation(): void
    {
        $path = sys_get_temp_dir().'/ezs-cancel-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $store = new GlobalQueueStore($path);
            $job=$store->enqueue('lab','analysis_job:9002','test.cancel.9002','profile','gpu');
            $this->assertNotNull($store->claim('gpu',120,(int)$job['id']));
            $this->expectExceptionMessage('active_executor_stop_attestation_required');
            $store->cancelQueued((int)$job['id'],'lab');
        } finally {
            unset($store);
            foreach (['','-wal','-shm'] as $suffix) @unlink($path.$suffix);
        }
    }
}
