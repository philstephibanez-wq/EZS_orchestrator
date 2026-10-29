<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\RootDevRecoveryDecision as Decision;
final class RootDevRecovery018Test extends TestCase
{
    public function testAbsentStateNeverAuthorizesRecovery(): void {self::assertSame('NO_STATE',Decision::inspect(null,[],[])['decision']);}
    public function testRecordedPidAliveRefusesRecoveryEvenWithoutListener(): void {
        $r=Decision::inspect(['php_pid'=>4948,'caddy_pid'=>1234], [['pid'=>4948,'created'=>'wmi','command'=>'irrelevant','executable'=>'irrelevant']],[]);
        self::assertSame('REFUSE',$r['decision']);self::assertContains('recorded_php_pid_active_4948',$r['reasons']);
    }
    public function testForeignListenerRefusesRecovery(): void {
        $r=Decision::inspect(['php_pid'=>111,'caddy_pid'=>222],[],[8790=>[444]]);
        self::assertSame('REFUSE',$r['decision']);self::assertContains('listener_8790_pid_444',$r['reasons']);
    }
    public function testNoProcessNoListenerIsOnlyCandidateNotPermission(): void {
        $r=Decision::inspect(['php_pid'=>111,'caddy_pid'=>222],[],[]);
        self::assertSame('COLD_START_CANDIDATE',$r['decision']);self::assertContains('requires_second_observation_and_lock',$r['reasons']);
    }
    public function testInvalidIdentityFailsClosed(): void {self::assertSame('REFUSE',Decision::inspect(['php_pid'=>0,'caddy_pid'=>1],[],[])['decision']);}
}
