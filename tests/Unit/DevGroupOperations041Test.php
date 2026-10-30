<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\DevGroupOperationsController;
use PHPUnit\Framework\TestCase;

final class DevGroupOperations041Test extends TestCase
{
    private function states(): array
    {
        return [
            'root_php' => 'ATTESTED',
            'root_caddy' => 'ATTESTED',
            'ezscore_dev' => 'ATTESTED',
            'ezscore_preview' => 'ATTESTED',
            'lab' => 'ATTESTED',
            'assistant' => 'ATTESTED',
        ];
    }

    public function testLoopbackAndDevAreMandatory(): void
    {
        self::assertTrue(DevGroupOperationsController::allowed('dev', '127.0.0.1', '127.0.0.1'));
        self::assertTrue(DevGroupOperationsController::allowed('dev', 'localhost', '::1'));
        self::assertFalse(DevGroupOperationsController::allowed('prod', '127.0.0.1', '127.0.0.1'));
        self::assertFalse(DevGroupOperationsController::allowed('dev', 'public.example', '127.0.0.1'));
        self::assertFalse(DevGroupOperationsController::allowed('dev', 'localhost', '192.168.0.1'));
    }

    public function testEachGroupIsIndependent(): void
    {
        $all = $this->states();
        foreach (['dev', 'lab', 'assistant'] as $group) {
            self::assertSame(['start'=>false,'restart'=>true,'stop'=>true,'state'=>'RUNNING'], DevGroupOperationsController::permission($all, $group));
        }
        $all['lab'] = 'ABSENT';
        self::assertSame(['start'=>true,'restart'=>false,'stop'=>false,'state'=>'STOPPED'], DevGroupOperationsController::permission($all, 'lab'));
        self::assertSame('RUNNING', DevGroupOperationsController::permission($all, 'dev')['state']);
        self::assertSame('RUNNING', DevGroupOperationsController::permission($all, 'assistant')['state']);
    }

    public function testPartialDevGroupRefusesUnsafeSharedCacheStart(): void
    {
        $states = $this->states();
        $states['ezscore_preview'] = 'ABSENT';
        self::assertSame(['start'=>false,'restart'=>false,'stop'=>true,'state'=>'PARTIAL'], DevGroupOperationsController::permission($states, 'dev'));
    }

    public function testAmbiguousUnrelatedOwnerBlocksEveryAction(): void
    {
        $states = $this->states();
        $states['root_caddy'] = 'PORT_UNVERIFIED';
        self::assertSame(['start'=>false,'restart'=>false,'stop'=>false,'state'=>'UNVERIFIED'], DevGroupOperationsController::permission($states, 'lab'));
    }

    public function testUnknownGroupRefused(): void
    {
        $this->expectException(InvalidArgumentException::class);
        DevGroupOperationsController::permission($this->states(), 'root');
    }
}
