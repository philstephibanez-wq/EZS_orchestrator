<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\RootDevRecoveryDecision;

final class RootTcpEvidence020Test extends TestCase
{
    public function testPidZeroIsReportedAsUnattributedNotAsProcess(): void
    {
        $res=RootDevRecoveryDecision::inspect(['php_pid'=>6340,'caddy_pid'=>17996],[],[8502=>[0]]);
        self::assertSame('REFUSE',$res['decision']);
        self::assertContains('listener_8502_owner_unattributed',$res['reasons']);
        self::assertNotContains('listener_8502_pid_0',$res['reasons']);
    }
    public function testEmptyListenersDoNotInventPidZero(): void
    {
        $res=RootDevRecoveryDecision::inspect(['php_pid'=>6340,'caddy_pid'=>17996],[],[]);
        self::assertSame('COLD_START_CANDIDATE',$res['decision']);
        self::assertNotContains('listener_8502_owner_unattributed',$res['reasons']);
    }
    public function testLivingResidualProcessesStillRefuseRecovery(): void
    {
        $res=RootDevRecoveryDecision::inspect(['php_pid'=>6340,'caddy_pid'=>17996],
            [['pid'=>6340],['pid'=>17996]],[]);
        self::assertSame('REFUSE',$res['decision']);
        self::assertContains('recorded_php_pid_active_6340',$res['reasons']);
        self::assertContains('recorded_caddy_pid_active_17996',$res['reasons']);
    }
    public function testRealListenerOwnerIsPreserved(): void
    {
        $res=RootDevRecoveryDecision::inspect(['php_pid'=>6340,'caddy_pid'=>17996],[],[8790=>[17996]]);
        self::assertContains('listener_8790_pid_17996',$res['reasons']);
    }
}
