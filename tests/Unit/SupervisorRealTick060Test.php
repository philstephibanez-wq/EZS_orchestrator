<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\DesiredServiceState;
use Ezs\Web\Module\Infrastructure\ServiceSupervisorCycle;
use PHPUnit\Framework\TestCase;

final class SupervisorRealTick060Test extends TestCase
{
    public function testColdBootHotBootCrashRecoveryAndIntentionalStopUseProductionTick(): void
    {
        $desired = array_fill_keys(DesiredServiceState::GROUPS, DesiredServiceState::STOPPED);
        $running = []; $spawn = []; $events = []; $retry = []; $writes = [];
        $start = static function (string $group) use (&$running, &$spawn): array {
            if (isset($running[$group])) return [];
            $running[$group] = true;
            $spawn[] = $group;
            return [$group => count($spawn)];
        };
        $log = static function (string $level, string $group, string $event) use (&$events): void {
            $events[] = $level.':'.$group.':'.$event;
        };
        $save = static function (array $new) use (&$retry, &$writes): void {
            $retry = $new;
            $writes[] = $new;
        };
        $emit = static function (string $line): void {};
        $cycle = static function (int $now) use (&$desired, &$retry, $start, $log, $save, $emit): int {
            return ServiceSupervisorCycle::run($desired, $retry, $now, $start, $log, $save, $emit);
        };

        self::assertSame(0, $cycle(1000)); // Cold boot defaults STOPPED.
        self::assertSame([], $spawn);
        $desired['root'] = 'RUNNING';
        $desired['dev'] = 'RUNNING';
        $desired['lab'] = 'RUNNING';
        $desired['prod'] = 'RUNNING';
        self::assertSame(0, $cycle(1001));
        self::assertSame(['root','dev','lab','prod'], $spawn); // Production ordering.
        self::assertSame(0, $cycle(1002)); // Warm boot is idempotent.
        self::assertCount(4, $spawn);
        unset($running['lab']); // Simulated crash.
        self::assertSame(0, $cycle(1003));
        self::assertSame(['root','dev','lab','prod','lab'], $spawn);
        $desired['lab'] = 'STOPPED'; // An operator stop persists into following cycles.
        unset($running['lab']);
        self::assertSame(0, $cycle(1004));
        self::assertCount(5, $spawn);
        self::assertSame([], $retry);
        self::assertNotEmpty($events);
        self::assertNotEmpty($writes);
    }

    public function testFailureBackoffDoesNotStartStoppedGroupOrBlockOtherGroups(): void
    {
        $desired = array_fill_keys(DesiredServiceState::GROUPS, DesiredServiceState::STOPPED);
        $desired['dev'] = 'RUNNING'; $desired['lab'] = 'RUNNING'; $desired['prod'] = 'RUNNING';
        $calls = []; $logs = []; $outputs = []; $persisted = [];
        $start = static function (string $group) use (&$calls): array {
            $calls[] = $group;
            if ($group === 'lab') throw new RuntimeException('LAB_DOWN');
            return [];
        };
        $log = static function (string $severity, string $group, string $message) use (&$logs): void {
            $logs[] = [$severity,$group,$message];
        };
        $save = static function (array $s) use (&$persisted): void { $persisted = $s; };
        $emit = static function (string $message) use (&$outputs): void { $outputs[] = $message; };
        self::assertSame(1, ServiceSupervisorCycle::run($desired, [], 1000, $start, $log, $save, $emit));
        self::assertSame(['dev','lab','prod'], $calls);
        self::assertSame(['count'=>1,'next'=>1030], $persisted['lab']);
        self::assertSame('ERROR', $logs[0][0]);
        $calls = [];
        self::assertSame(0, ServiceSupervisorCycle::run($desired, $persisted, 1010, $start, $log, $save, $emit));
        self::assertSame(['dev','prod'], $calls);
        self::assertContains('EZS_SUPERVISOR_BACKOFF_lab until=1030', $outputs);
        $calls = [];
        self::assertSame(1, ServiceSupervisorCycle::run($desired, $persisted, 1031, $start, $log, $save, $emit));
        self::assertSame(['dev','lab','prod'], $calls);
        self::assertSame(['count'=>2,'next'=>1091], $persisted['lab']);
    }

    public function testPersistFailureCannotBeReportedAsSuccess(): void
    {
        $desired = array_fill_keys(DesiredServiceState::GROUPS, 'STOPPED');
        $desired['root'] = 'RUNNING';
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('STORAGE_FAILED');
        ServiceSupervisorCycle::run($desired, [], 1000,
            static fn(string $group): array => [],
            static function (string $level, string $group, string $event): void {},
            static function (array $s): void {throw new RuntimeException('STORAGE_FAILED');},
            static function (string $line): void {}
        );
    }
}
