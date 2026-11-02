<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExecutorStopAttestor;
use Ezs\Web\Module\Coordination\WindowsExecutorObservation;
use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;
use PHPUnit\Framework\TestCase;

final class WindowsExecutorDescendantsTest extends TestCase
{
    private const OWNER = [
        'id'=>14, 'claim_generation'=>3, 'node'=>'MAIN', 'pid'=>4100,
        'created_at'=>'20261102090000.000000+060', 'instance_id'=>'synthetic-14',
    ];

    private static function row(int $pid, int $parent, string $created = '20261102090100.000000+060'): array
    {
        return ['ProcessId'=>$pid,'ParentProcessId'=>$parent,'CreationDate'=>$created,
            'ExecutablePath'=>'C:\\PHP\\php.exe','CommandLine'=>'php fixture.php'];
    }

    private function observe(array $rows): array
    {
        $observer = new WindowsExecutorObservation(new WindowsProcessInventory(static fn(): array => $rows), 'MAIN');
        $result = $observer->observe(self::OWNER);
        self::assertFalse((new ExecutorStopAttestor($observer->asProbe(), self::OWNER))->attest(self::OWNER));
        return $result;
    }

    public function testOrphanDirectDescendantDoesNotPermitRecovery(): void
    {
        $result = $this->observe([self::row(4200, 4100)]);
        self::assertSame('unknown', $result['status']);
        self::assertSame('possible_descendant_still_running', $result['reason']);
    }

    public function testNestedDescendantsDoNotPermitRecovery(): void
    {
        $result = $this->observe([self::row(4200, 4100), self::row(4300, 4200)]);
        self::assertSame('possible_descendant_still_running', $result['reason']);
    }

    public function testAbsentTreeAndReusedPidRemainUnknown(): void
    {
        $empty = $this->observe([]);
        self::assertSame('pid_missing_tree_unverified', $empty['reason']);
        $reused = $this->observe([self::row(4100, 1), self::row(4200, 4100)]);
        self::assertSame('pid_reused_or_timestamp_mismatch', $reused['reason']);
    }

    public function testCyclicParentDataNeverLoopsOrAttestsStopped(): void
    {
        $result = $this->observe([self::row(4200, 4300), self::row(4300, 4200)]);
        self::assertSame('pid_missing_tree_unverified', $result['reason']);
    }
}
