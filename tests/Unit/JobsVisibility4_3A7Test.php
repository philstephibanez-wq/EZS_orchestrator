<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueDashboard;
use PHPUnit\Framework\TestCase;

final class JobsVisibility4_3A7Test extends TestCase
{
    public function testMissingDatabaseNeverCreatesQueue(): void
    {
        $path = sys_get_temp_dir().'/ezs-jobs-visibility-missing-'.bin2hex(random_bytes(6)).'.sqlite';
        $result = GlobalQueueDashboard::read($path);
        self::assertFalse($result['available']);
        self::assertSame('queue_database_missing', $result['reason']);
        self::assertFileDoesNotExist($path);
    }

    public function testExpiredLeaseIsVisibleButNeverRecovered(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite required');
        $dir = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $path = tempnam($dir, 'ezs-jobs-vis-');
        self::assertIsString($path);
        try {
            $pdo = new \PDO('sqlite:'.$path);
            $pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
            $pdo->exec('CREATE TABLE global_queue_jobs (id INTEGER PRIMARY KEY,producer TEXT,external_id TEXT,kind TEXT,priority INTEGER,resource_class TEXT,state TEXT,claim_generation INTEGER,lease_until INTEGER,created_at INTEGER,updated_at INTEGER)');
            $pdo->exec('CREATE TABLE global_queue_events (event_id INTEGER PRIMARY KEY,job_id INTEGER,progress_percent INTEGER,phase TEXT,created_at INTEGER)');
            $pdo->prepare('INSERT INTO global_queue_jobs VALUES (1,?,?,?,?,?,?,?,?,?,?)')->execute(['lab','analysis_job:202','profile',50,'gpu','running',1,time()-100,time()-200,time()-100]);
            $result = GlobalQueueDashboard::read($path);
            self::assertTrue($result['available']);
            self::assertSame(1, $result['counts']['running']);
            self::assertSame(1, $result['counts']['expired']);
            self::assertTrue($result['jobs'][0]['lease_expired']);
            self::assertSame('running', $pdo->query('SELECT state FROM global_queue_jobs WHERE id=1')->fetchColumn());
            $pdo = null;
        } finally {
            unset($pdo);
            foreach ([$path, $path.'-wal', $path.'-shm'] as $file) if (is_file($file)) @unlink($file);
        }
    }
}
