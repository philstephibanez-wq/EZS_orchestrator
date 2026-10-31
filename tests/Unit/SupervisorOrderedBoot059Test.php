<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\DesiredServiceState;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Ezs\Web\Module\Infrastructure\ServiceSupervisorCommand;
use PHPUnit\Framework\TestCase;

/** Simulates the ordered boot using the real native lifecycle and injected Windows observations. */
final class SupervisorOrderedBoot059Test extends TestCase
{
    public function testColdBootWarmBootCrashStopAndForeignPidInBootOrder(): void
    {
        $base = sys_get_temp_dir().'/ezs-ordered-'.bin2hex(random_bytes(7));
        self::assertTrue(mkdir($base));
        self::assertTrue(mkdir($base.'/dev'));
        self::assertTrue(mkdir($base.'/prod'));
        $desired = new DesiredServiceState($base.'/desired.json');
        $alive = []; $nextPid = 30000; $spawned = []; $terminated = [];
        $devSpecs = NativeWindowsLifecycle::specs();
        $prodSpecs = NativeWindowsLifecycle::prodSpecs();
        $specs = array_merge($devSpecs, $prodSpecs);
        $inventory = static function () use (&$alive): array {
            $rows = [];
            foreach ($alive as $pid => $spec) {
                $args = [$spec['exe'], ...NativeWindowsLifecycle::spawnArguments($spec['args'])];
                $rows[] = ['pid'=>$pid, 'created'=>'created-'.$pid, 'executable'=>$spec['exe'],
                    'command'=>implode(' ', array_map(static fn(string $a): string => '"'.$a.'"', $args))];
            }
            return $rows;
        };
        $listeners = static function () use (&$alive): array {
            $ports = [];
            foreach ($alive as $pid => $spec) {
                foreach ([$spec['port'], ...($spec['additional_ports'] ?? [])] as $port) $ports[$port] = [$pid];
            }
            return $ports;
        };
        $spawn = static function (string $exe, string $args, string $cwd) use (&$alive, &$nextPid, &$spawned, $specs): int {
            foreach ($specs as $name => $spec) {
                if ($spec['exe'] === $exe && $spec['args'] === $args && $spec['cwd'] === $cwd) {
                    $pid = ++$nextPid;
                    $alive[$pid] = $spec;
                    $spawned[] = $name;
                    return $pid;
                }
            }
            throw new RuntimeException('UNEXPECTED_SPAWN');
        };
        $terminate = static function (int $pid) use (&$alive, &$terminated): bool {
            $terminated[] = $pid;
            unset($alive[$pid]);
            return true;
        };
        $make = static function (string $profile) use ($base, $inventory, $listeners, $spawn, $terminate): NativeWindowsLifecycle {
            return new NativeWindowsLifecycle($inventory, $listeners, $spawn, $terminate,
                $base.'/'.$profile, static fn(): bool => true, static fn(): ?int => null, $profile);
        };
        $dev = $make('dev'); $prod = $make('prod');
        $cycle = static function () use ($desired, $dev, $prod): void {
            foreach (ServiceSupervisorCommand::planned($desired->all()) as $group) {
                if ($group === 'assistant_ai') continue; // distinct engine: not injected in this test
                ($group === 'prod' ? $prod : $dev)->startGroup($group);
            }
        };
        try {
            // Cold boot: STOPPED is authoritative and cannot spawn anything.
            $cycle();
            self::assertSame([], $spawned);
            $desired->setMany(['root'=>'RUNNING', 'dev'=>'RUNNING', 'lab'=>'RUNNING',
                'assistant'=>'RUNNING', 'prod'=>'RUNNING']);
            $cycle();
            self::assertSame(['root_php','root_caddy','ezscore_dev','ezscore_preview',
                'lab','assistant','prod_backend','prod_gateway','prod_caddy'], $spawned);
            self::assertCount(9, $alive);
            // Warm boot must be idempotent and must not terminate or duplicate processes.
            $cycle();
            self::assertCount(9, $spawned);
            self::assertSame([], $terminated);
            // Unexpected LAB crash: stale proof is reconciled, ONLY LAB restarts.
            $labPid = array_search($devSpecs['lab'], $alive, true);
            self::assertIsInt($labPid);
            unset($alive[$labPid]);
            $cycle();
            self::assertSame('lab', end($spawned));
            self::assertCount(10, $spawned);
            self::assertCount(9, $alive);
            self::assertSame([], $terminated);
            self::assertStringContainsString('DEAD_RECORD lab PID='.$labPid,
                (string)file_get_contents($base.'/dev/native-reconciled.log'));
            // Operator STOPPED always wins, even after a subsequent simulated reboot.
            $desired->set('lab', DesiredServiceState::STOPPED);
            $dev->stopGroup('lab');
            $before = count($spawned);
            $cycle();
            self::assertSame($before, count($spawned));
            self::assertSame('STOPPED', (new DesiredServiceState($base.'/desired.json'))->get('lab'));
            // A changed PID belonging to a foreign process is refused, never terminated.
            $caddyPid = array_search($prodSpecs['prod_caddy'], $alive, true);
            self::assertIsInt($caddyPid);
            $alive[$caddyPid]['exe'] = 'C:/foreign.exe';
            $beforeTerminated = count($terminated);
            try {
                $cycle();
                self::fail('FOREIGN_PID_MUST_BE_REFUSED');
            } catch (RuntimeException $e) {
                self::assertStringContainsString('IDENTITY_UNVERIFIED_prod_caddy', $e->getMessage());
            }
            self::assertCount($beforeTerminated, $terminated);
        } finally {
            foreach (['dev','prod'] as $profile) {
                foreach (glob($base.'/'.$profile.'/*') ?: [] as $file) if (is_file($file)) unlink($file);
                rmdir($base.'/'.$profile);
            }
            foreach (glob($base.'/*') ?: [] as $file) if (is_file($file)) unlink($file);
            rmdir($base);
        }
    }
}
