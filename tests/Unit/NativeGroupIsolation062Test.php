<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class NativeGroupIsolation062Test extends TestCase
{
    public function testStaleOccupiedRootDoesNotBlockIndependentLabButRootRemainsRefused(): void
    {
        $dir = sys_get_temp_dir().'/ezs-r8f25-'.bin2hex(random_bytes(6));
        self::assertTrue(mkdir($dir));
        $root = NativeWindowsLifecycle::specs()['root_php'];
        $lab = NativeWindowsLifecycle::specs()['lab'];
        $created = [];
        $spawnCount = 0;
        $terminateCount = 0;
        $inventory = static function () use (&$created): array {
            $rows = [];
            foreach ($created as $pid => $spec) {
                $argv = [$spec['exe'], ...NativeWindowsLifecycle::spawnArguments($spec['args'])];
                $rows[] = [
                    'pid' => $pid,
                    'created' => 'created-'.$pid,
                    'executable' => $spec['exe'],
                    'command' => implode(' ', array_map(static fn(string $a): string => '"'.$a.'"', $argv)),
                ];
            }
            return $rows;
        };
        $listeners = static function () use (&$created, $root): array {
            $ports = [$root['port'] => [26360]]; // A root port with no WMI identity.
            foreach ($created as $pid => $spec) $ports[$spec['port']] = [$pid];
            return $ports;
        };
        $spawn = static function (string $exe, string $args, string $cwd) use (&$created, &$spawnCount, $lab): int {
            self::assertSame($lab['exe'], $exe);
            self::assertSame($lab['args'], $args);
            self::assertSame($lab['cwd'], $cwd);
            ++$spawnCount;
            $created[9212] = $lab;
            return 9212;
        };
        $terminate = static function (int $pid) use (&$terminateCount): bool {
            ++$terminateCount;
            return true;
        };
        $service = new NativeWindowsLifecycle(
            $inventory, $listeners, $spawn, $terminate, $dir,
            static fn(string $exe, string $cwd): bool => true,
            static fn(int $port): ?int => null
        );
        try {
            file_put_contents($dir.'/native-processes.json', json_encode([
                'schema'=>'ezs.native.dev.v1',
                'records'=>['root_php'=>['pid'=>26360,'created'=>'old-created']],
            ], JSON_THROW_ON_ERROR));

            $started = $service->startGroup('lab');
            self::assertSame(['lab'=>9212], $started);
            self::assertSame(1, $spawnCount);
            self::assertSame(0, $terminateCount);
            self::assertSame([], $service->startGroup('lab'));
            self::assertSame('ATTESTED', $service->status()['lab']);
            self::assertSame('PORT_UNVERIFIED', $service->status()['root_php']);

            $records = json_decode((string)file_get_contents($dir.'/native-processes.json'),true,512,JSON_THROW_ON_ERROR)['records'];
            self::assertSame(26360, $records['root_php']['pid']);
            self::assertSame(9212, $records['lab']['pid']);
            self::assertFileDoesNotExist($dir.'/native-spawn-pending.json');

            try {
                $service->startGroup('root');
                self::fail('Unverified ROOT must remain blocked');
            } catch (RuntimeException $e) {
                self::assertSame('EZS_NATIVE_STALE_PORT_OCCUPIED_root_php', $e->getMessage());
            }
            self::assertSame(1, $spawnCount);
            self::assertSame(0, $terminateCount);
        } finally {
            foreach (glob($dir.'/*') ?: [] as $p) {
                if (is_file($p)) unlink($p);
            }
            if (is_dir($dir)) rmdir($dir);
        }
    }
}
