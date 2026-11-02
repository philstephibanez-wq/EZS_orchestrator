<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Coordination;

use Ezs\Web\Module\Infrastructure\WindowsProcessInventory;

/**
 * Read-only local Windows observation for the strict attestor.
 * A missing PID is NOT proof that the original execution tree has stopped.
 */
final class WindowsExecutorObservation
{
    public function __construct(
        private readonly WindowsProcessInventory $inventory,
        private readonly string $localNode,
    ) {
        if ($localNode === '' || strlen($localNode) > 128) {
            throw new \InvalidArgumentException('invalid_windows_observer_node');
        }
    }

    /** @param array<string,mixed> $ownership */
    public function observe(array $ownership): array
    {
        $pid = filter_var($ownership['pid'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        $created = $ownership['created_at'] ?? null;
        $instance = $ownership['instance_id'] ?? null;
        if (($ownership['node'] ?? null) !== $this->localNode || $pid === false
            || !is_string($created) || $created === '' || !is_string($instance) || $instance === '') {
            return ['status' => 'unknown', 'reason' => 'identity_or_node_unverifiable'];
        }
        try {
            $rows = $this->inventory->collect();
        } catch (\Throwable) {
            return ['status' => 'unknown', 'reason' => 'inventory_unavailable'];
        }
        foreach ($rows as $row) {
            if ($row['pid'] !== $pid) {
                continue;
            }
            if (!hash_equals($created, $row['created'])) {
                return ['status' => 'unknown', 'reason' => 'pid_reused_or_timestamp_mismatch'];
            }
            return [
                'status' => 'running_confirmed',
                'node' => $this->localNode,
                'pid' => $pid,
                'created_at' => $created,
                'instance_id' => $instance,
            ];
        }
        // No process inventory snapshot can establish whether a descendant survived.
        return ['status' => 'unknown', 'reason' => 'pid_missing_tree_unverified'];
    }

    /** Adapter for TrustedLeaseRecovery's independent probe callback. */
    public function asProbe(): \Closure
    {
        return fn(array $ownership): array => $this->observe($ownership);
    }
}
