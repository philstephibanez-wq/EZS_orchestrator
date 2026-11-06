<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

/** Replacement for obsolete GPU/CPU parallelism contract: global FIFO regardless of capability. */
final class GlobalQueueGpuSlotTest extends TestCase
{
    public function testGlobalExclusivityAndArrivalOrderAcrossResourceClasses(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite_required');
        $root = PHP_OS_FAMILY === 'Windows' ? 'H:/temp' : sys_get_temp_dir();
        $file = $root.'/ezs-global-fifo-'.bin2hex(random_bytes(8)).'.sqlite';
        try {
            $a = new GlobalQueueStore($file);
            $b = new GlobalQueueStore($file);
            $first = $a->enqueue('lab','test-first','fifo-first','profile','gpu',10);
            $second = $a->enqueue('lab','test-second','fifo-second','profile','cpu',99);
            $third = $a->enqueue('lab','test-third','fifo-third','profile','gpu',99);
            self::assertNull($a->claim('cpu')); // CPU cannot overtake FIFO head GPU.
            $running = $a->claim('gpu');
            self::assertSame((int)$first['id'],(int)$running['id']);
            self::assertNull($b->claim('cpu'));
            self::assertNull($b->claim('gpu'));
            $a->finish((int)$running['id'],(string)$running['lease_token'],true);
            $next = $b->claim('cpu');
            self::assertSame((int)$second['id'],(int)$next['id']);
            self::assertNull($a->claim('gpu'));
            $b->finish((int)$next['id'],(string)$next['lease_token'],false);
            self::assertSame((int)$third['id'],(int)$a->claim('gpu')['id']);
        } finally {
            unset($a,$b);
            foreach ([$file,$file.'-wal',$file.'-shm'] as $path) if(is_file($path)) @unlink($path);
        }
    }
}
