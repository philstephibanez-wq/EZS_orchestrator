<?php
declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\ExecutorStopAttestor;
use PHPUnit\Framework\TestCase;

final class ExecutorStopAttestorTest extends TestCase
{
    private function ownership(): array
    {
        return ['id' => 10, 'claim_generation' => 2, 'node' => 'MAIN', 'pid' => 123,
            'created_at' => '2026-11-02T01:00:00Z', 'instance_id' => 'spawn-7'];
    }

    public function testExactIndependentStoppedObservationAccepted(): void
    {
        $identity = $this->ownership();
        $attestor = new ExecutorStopAttestor(static fn (array $owner): array => [
            'status' => 'stopped_confirmed', 'node' => $owner['node'], 'pid' => $owner['pid'],
            'created_at' => $owner['created_at'], 'instance_id' => $owner['instance_id'],
        ], $identity);
        self::assertTrue($attestor->attest(['id' => 10, 'claim_generation' => 2]));
        self::assertFalse($attestor->attest(['id' => 10, 'claim_generation' => 3]));
    }

    public function testUnknownAliveOrReusedPidFailsClosed(): void
    {
        foreach (['unknown', 'running', 'stopped_confirmed'] as $status) {
            $attestor = new ExecutorStopAttestor(static fn (): array => [
                'status' => $status, 'node' => 'MAIN', 'pid' => 123,
                'created_at' => 'DIFFERENT', 'instance_id' => 'spawn-7',
            ], $this->ownership());
            self::assertFalse($attestor->attest(['id' => 10, 'claim_generation' => 2]));
        }
        $attestor = new ExecutorStopAttestor(static function (): array {
            throw new \RuntimeException('offline');
        }, $this->ownership());
        self::assertFalse($attestor->attest(['id' => 10, 'claim_generation' => 2]));
    }
}
