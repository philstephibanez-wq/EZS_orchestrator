<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class NativeFailureGate033Test extends TestCase
{
    private string $runtime;

    protected function setUp(): void
    {
        $this->runtime = sys_get_temp_dir().'/ezs-r8f5-'.bin2hex(random_bytes(8));
        self::assertTrue(mkdir($this->runtime));
    }

    protected function tearDown(): void
    {
        foreach (glob($this->runtime.'/*') ?: [] as $file) {
            if (is_file($file)) unlink($file);
        }
        if (is_dir($this->runtime)) rmdir($this->runtime);
    }

    public function testThirdSpawnFailurePreservesEvidenceAndSafelyRecoversWhenCandidateAbsent(): void
    {
        $specs = NativeWindowsLifecycle::specs();
        $spawned = [];
        $spawnCount = 0;
        $terminated = 0;
        $inventory = static function () use (&$spawned): array {
            $rows = [];
            foreach ($spawned as $pid => $spec) {
                $rows[] = [
                    'pid' => $pid,
                    'created' => '20261030010000.000000+060',
                    'executable' => $spec['exe'],
                    'command' => '"'.$spec['exe'].'" '.$spec['args'],
                ];
            }
            return $rows;
        };
        $listeners = static function () use (&$spawned): array {
            $ports = [];
            foreach ($spawned as $pid => $spec) $ports[$spec['port']] = [$pid];
            return $ports;
        };
        $spawn = static function (string $exe, string $args, string $cwd) use (&$spawnCount, &$spawned, $specs): int {
            ++$spawnCount;
            if ($spawnCount === 3) throw new \RuntimeException('EZS_INJECTED_THIRD_SPAWN_FAILURE');
            foreach ($specs as $spec) {
                if ($spec['exe'] === $exe && $spec['args'] === $args && $spec['cwd'] === $cwd) {
                    $pid = 7000 + $spawnCount;
                    $spawned[$pid] = $spec;
                    return $pid;
                }
            }
            throw new \RuntimeException('EZS_UNKNOWN_SIMULATED_SPAWN');
        };
        $service = new NativeWindowsLifecycle(
            $inventory, $listeners, $spawn,
            static function (int $pid) use (&$terminated): bool { ++$terminated; return true; },
            $this->runtime,
            static fn(string $exe, string $cwd): bool => true,
            // Aucun appel TCP réel : les propriétaires sont produits par $listeners.
            static fn(int $port): ?int => null
        );

        try {
            $service->start();
            self::fail('Third injected creation must fail');
        } catch (\RuntimeException $e) {
            self::assertSame('EZS_INJECTED_THIRD_SPAWN_FAILURE', $e->getMessage());
        }
        self::assertSame(3, $spawnCount);
        self::assertSame(0, $terminated);
        self::assertFileExists($this->runtime.'/native-spawn-pending.json');
        $pending = json_decode((string)file_get_contents($this->runtime.'/native-spawn-pending.json'), true, 512, JSON_THROW_ON_ERROR);
        self::assertSame('ezscore_dev', $pending['name']);
        $stored = json_decode((string)file_get_contents($this->runtime.'/native-processes.json'), true, 512, JSON_THROW_ON_ERROR);
        self::assertCount(2, $stored['records']);

        // stop/status sont interdits tant qu'un journal pending subsiste.
        foreach (['stop', 'status'] as $action) {
            try {
                $service->$action();
                self::fail('Pending evidence must block '.$action);
            } catch (\RuntimeException $e) {
                self::assertSame('EZS_NATIVE_PENDING_REQUIRES_MANUAL_ATTESTATION', $e->getMessage());
            }
        }
        self::assertSame(3, $spawnCount);
        self::assertSame(0, $terminated);

        // start() réconcilie le pending uniquement si le candidat est absent.
        $restarted = $service->start();
        self::assertSame(7, $spawnCount);
        self::assertSame(0, $terminated);
        self::assertCount(4, $restarted);
        self::assertSame(7004, $restarted['ezscore_dev']);
        self::assertFileDoesNotExist($this->runtime.'/native-spawn-pending.json');
        $after = json_decode((string)file_get_contents($this->runtime.'/native-processes.json'), true, 512, JSON_THROW_ON_ERROR);
        self::assertCount(count($specs), $after['records']);
        self::assertSame('ATTESTED', $service->status()['ezscore_dev']);
        self::assertStringContainsString('ABANDONED_PENDING ezscore_dev', (string)file_get_contents($this->runtime.'/native-reconciled.log'));
    }

    public function testForeignListenerRefusesWithoutSpawningOrChangingEvidence(): void
    {
        $spawnCount = 0;
        $service = new NativeWindowsLifecycle(
            static fn(): array => [],
            static fn(): array => [8791 => [4301]],
            static function () use (&$spawnCount): int { ++$spawnCount; return 999; },
            static fn(int $pid): bool => true,
            $this->runtime,
            static fn(string $exe, string $cwd): bool => true,
            static fn(int $port): ?int => null
        );
        try {
            $service->start();
            self::fail('Foreign listener must block start');
        } catch (\RuntimeException $e) {
            self::assertSame('EZS_NATIVE_START_REFUSED_PORT_root_php', $e->getMessage());
        }
        self::assertSame(0, $spawnCount);
        self::assertFileDoesNotExist($this->runtime.'/native-spawn-pending.json');
    }

    public function testPidReuseIsRejectedByStrongAttestation(): void
    {
        $spec = NativeWindowsLifecycle::specs()['lab'];
        $observed = [
            'pid' => 7100, 'created' => '20261030020000.000000+060',
            'executable' => $spec['exe'], 'command' => '"'.$spec['exe'].'" '.$spec['args']
        ];
        self::assertFalse(NativeWindowsLifecycle::attest(
            ['pid' => 7100, 'created' => '20261030010000.000000+060'],
            $spec, $observed, [8701 => [7100]]
        ));
    }
}
