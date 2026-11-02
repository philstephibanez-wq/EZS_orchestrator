<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExecutorStopAttestor;
use Ezs\Web\Module\Coordination\WindowsExecutorObservation;
use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;
use PHPUnit\Framework\TestCase;

final class WindowsExecutorObservationTest extends TestCase
{
    private const OWNER = [
        'id' => 10, 'claim_generation' => 2, 'node' => 'MAIN',
        'pid' => 4120, 'created_at' => '20261102080000.000000+060', 'instance_id' => 'run-10',
    ];

    private function observer(array $rows): WindowsExecutorObservation
    {
        return new WindowsExecutorObservation(new WindowsProcessInventory(static fn(): array => $rows), 'MAIN');
    }

    private static function row(int $pid, string $created): array
    {
        return [
            'ProcessId' => $pid, 'ParentProcessId' => 1, 'CreationDate' => $created,
            'ExecutablePath' => 'C:\\PHP\\php.exe', 'CommandLine' => 'php fixture.php',
        ];
    }

    public function testMatchingLiveProcessBlocksAttestation(): void
    {
        $probe = $this->observer([self::row(4120, self::OWNER['created_at'])]);
        $observed = $probe->observe(self::OWNER);
        self::assertSame('running_confirmed', $observed['status']);
        self::assertSame(4120, $observed['pid']);
        self::assertFalse((new ExecutorStopAttestor($probe->asProbe(), self::OWNER))->attest(self::OWNER));
    }

    public function testMissingProcessAndReusedPidNeverAttestStopped(): void
    {
        foreach ([[], [self::row(4120, '20261102080100.000000+060')]] as $rows) {
            $probe = $this->observer($rows);
            self::assertSame('unknown', $probe->observe(self::OWNER)['status']);
            self::assertFalse((new ExecutorStopAttestor($probe->asProbe(), self::OWNER))->attest(self::OWNER));
        }
    }

    public function testForeignNodeAndBrokenInventoryFailClosed(): void
    {
        $foreign = self::OWNER;
        $foreign['node'] = 'XPS';
        self::assertSame('unknown', $this->observer([])->observe($foreign)['status']);
        $failed = new WindowsExecutorObservation(new WindowsProcessInventory(static function (): array {
            throw new \RuntimeException('WMI access denied');
        }), 'MAIN');
        self::assertSame('unknown', $failed->observe(self::OWNER)['status']);
        self::assertFalse((new ExecutorStopAttestor($failed->asProbe(), self::OWNER))->attest(self::OWNER));
    }
}
