<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\QueueExecutorProtocol;
use PHPUnit\Framework\TestCase;

final class QueueProfileExactClaim4_3A5Test extends TestCase
{
    public function testExactClaimCannotOvertakeFifoHead(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite_required');
        $root = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $file = $root.'/ezs-profile-claim-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $q = new GlobalQueueStore($file);
            $first = $q->enqueue('lab','analysis_job:903','test.profile.903','profile','gpu',10);
            $second = $q->enqueue('lab','analysis_job:904','test.profile.904','profile','gpu',99);
            $late = QueueExecutorProtocol::claimInput(['resource_class'=>'gpu','lease_seconds'=>120,'job_id'=>(int)$second['id'],'kind'=>'profile']);
            self::assertNull(QueueExecutorProtocol::claim($q,$late));
            $head = QueueExecutorProtocol::claimInput(['resource_class'=>'gpu','lease_seconds'=>120,'job_id'=>(int)$first['id'],'kind'=>'profile']);
            $running = QueueExecutorProtocol::claim($q,$head);
            self::assertIsArray($running);
            self::assertSame((int)$first['id'],$running['id']);
            self::assertNull(QueueExecutorProtocol::claim($q,$late));
            $q->finish($running['id'],$running['lease_token'],true);
            self::assertSame((int)$second['id'],QueueExecutorProtocol::claim($q,$late)['id']);
        } finally {
            unset($q);
            foreach ([$file,$file.'-wal',$file.'-shm'] as $path) if(is_file($path)) @unlink($path);
        }
    }
    public function testLegacyClaimShapeRemainsValidated(): void
    {
        $input=['resource_class'=>'cpu','lease_seconds'=>60];
        self::assertSame($input,QueueExecutorProtocol::claimInput($input));
        $this->expectException(\InvalidArgumentException::class);
        QueueExecutorProtocol::claimInput($input+['kind'=>'profile']);
    }
}
