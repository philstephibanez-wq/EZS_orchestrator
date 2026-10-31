<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\ServiceSupervisorCycle;
use PHPUnit\Framework\TestCase;

final class SupervisorJournalFailure061Test extends TestCase
{
    public function testJournalFailureAfterSuccessfulStartIsNotClassifiedAsStartFailure(): void
    {
        $started = [];
        $saved = [];
        $desired = ['root' => 'RUNNING'];
        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('JOURNAL_UNAVAILABLE');
        try {
            ServiceSupervisorCycle::run(
                $desired, [], 1000,
                static function (string $group) use (&$started): array {
                    $started[] = $group;
                    return ['root_php' => 1234];
                },
                static function (string $level, string $group, string $message): void {
                    throw new RuntimeException('JOURNAL_UNAVAILABLE');
                },
                static function (array $state) use (&$saved): void { $saved[] = $state; },
                static function (string $line): void {}
            );
        } finally {
            self::assertSame(['root'], $started);
            self::assertSame([], $saved);
        }
    }

    public function testFailedStartRemainsAStartFailureAndSchedulesRetry(): void
    {
        $events = [];
        $saved = [];
        $code = ServiceSupervisorCycle::run(
            ['lab' => 'RUNNING'], [], 1000,
            static function (string $group): array { throw new RuntimeException('START_UNAVAILABLE'); },
            static function (string $level, string $group, string $message) use (&$events): void {
                $events[] = [$level, $group, $message];
            },
            static function (array $state) use (&$saved): void { $saved = $state; },
            static function (string $line): void {}
        );
        self::assertSame(1, $code);
        self::assertSame(['count' => 1, 'next' => 1030], $saved['lab']);
        self::assertSame('ERROR', $events[0][0]);
        self::assertSame('lab', $events[0][1]);
        self::assertStringContainsString('START_FAILED START_UNAVAILABLE', $events[0][2]);
    }
}
