<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class NativeGroupLifecycle040Test extends TestCase
{
    private string $runtime;
    private array $live = [];
    private array $stopped = [];
    private int $nextPid = 9000;

    protected function setUp(): void
    {
        $this->runtime = sys_get_temp_dir().'/ezs-r8f11-'.bin2hex(random_bytes(8));
        self::assertTrue(mkdir($this->runtime));
    }

    protected function tearDown(): void
    {
        foreach (glob($this->runtime.'/*') ?: [] as $file) {
            if (is_file($file)) unlink($file);
        }
        if (is_dir($this->runtime)) rmdir($this->runtime);
    }

    private function lifecycle(): NativeWindowsLifecycle
    {
        $inventory = function (): array {
            $rows = [];
            foreach ($this->live as $pid => $spec) {
                $parts = [ $spec['exe'], ...NativeWindowsLifecycle::spawnArguments($spec['args']) ];
                $rows[] = [
                    'pid' => $pid,
                    'created' => '20261030090000.000000+060',
                    'executable' => $spec['exe'],
                    'command' => implode(' ', array_map(static fn(string $x): string => '"'.$x.'"', $parts)),
                ];
            }
            return $rows;
        };
        $listeners = function (): array {
            $ports = [];
            foreach ($this->live as $pid => $spec) $ports[$spec['port']] = [$pid];
            return $ports;
        };
        $spawn = function (string $exe, string $args, string $cwd): int {
            foreach (NativeWindowsLifecycle::specs() as $spec) {
                if ($spec['exe'] === $exe && $spec['args'] === $args && $spec['cwd'] === $cwd) {
                    $pid = ++$this->nextPid;
                    $this->live[$pid] = $spec;
                    return $pid;
                }
            }
            throw new LogicException('unexpected spawn');
        };
        $terminate = function (int $pid): bool {
            $this->stopped[] = $pid;
            unset($this->live[$pid]);
            return true;
        };
        return new NativeWindowsLifecycle($inventory, $listeners, $spawn, $terminate,
            $this->runtime, static fn(string $exe, string $cwd): bool => true,
            static fn(int $port): ?int => null);
    }

    public function testOnlyExplicitGroupsWithoutRootOrProd(): void
    {
        self::assertSame(['ezscore_dev', 'ezscore_preview'], NativeWindowsLifecycle::groups()['dev']);
        self::assertSame(['lab'], NativeWindowsLifecycle::groups()['lab']);
        self::assertSame(['assistant'], NativeWindowsLifecycle::groups()['assistant']);
        $all = array_merge(...array_values(NativeWindowsLifecycle::groups()));
        foreach (['root_php', 'root_caddy'] as $name) self::assertNotContains($name, $all);
    }

    public function testIndividualStartIsIdempotentAndDoesNotStartOtherGroups(): void
    {
        $svc = $this->lifecycle();
        $result = $svc->startGroup('lab');
        self::assertSame(['lab'], array_keys($result));
        self::assertCount(1, $this->live);
        self::assertSame([], $svc->startGroup('lab'));
        self::assertSame('ATTESTED', $svc->status()['lab']);
        self::assertSame('ABSENT', $svc->status()['assistant']);
    }

    public function testStoppingLabPreservesDevAndAssistant(): void
    {
        $svc = $this->lifecycle();
        $dev = $svc->startGroup('dev');
        $lab = $svc->startGroup('lab');
        $assistant = $svc->startGroup('assistant');
        self::assertSame($lab, $svc->stopGroup('lab'));
        self::assertSame([$lab['lab']], $this->stopped);
        foreach (array_merge($dev, $assistant) as $pid) self::assertArrayHasKey($pid, $this->live);
        self::assertSame([], $svc->stopGroup('lab'));
        self::assertSame('ATTESTED', $svc->status()['assistant']);
    }

    public function testUnknownGroupCannotCreateOrStopProcesses(): void
    {
        $svc = $this->lifecycle();
        $this->expectExceptionMessage('EZS_NATIVE_GROUP_REFUSED');
        $svc->stopGroup('root_caddy');
    }

    public function testUnknownGroupCannotStartProcesses(): void
    {
        $svc = $this->lifecycle();
        $this->expectExceptionMessage('EZS_NATIVE_GROUP_REFUSED');
        $svc->startGroup('prod');
    }

    public function testTamperedIdentityRefusesStopWithoutTermination(): void
    {
        $svc = $this->lifecycle();
        $lab = $svc->startGroup('lab');
        $pid = $lab['lab'];
        $stateFile = $this->runtime.'/native-processes.json';
        $state = json_decode((string)file_get_contents($stateFile), true, 512, JSON_THROW_ON_ERROR);
        $state['records']['lab']['created'] = 'forged';
        file_put_contents($stateFile, json_encode($state, JSON_THROW_ON_ERROR));
        try {
            $svc->stopGroup('lab');
            self::fail('Tampered identity must be refused');
        } catch (RuntimeException $e) {
            self::assertSame('EZS_NATIVE_GROUP_STOP_REFUSED_UNVERIFIED_lab', $e->getMessage());
        }
        self::assertSame([], $this->stopped);
        self::assertArrayHasKey($pid, $this->live);
    }
}
