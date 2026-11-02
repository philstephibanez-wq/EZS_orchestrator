<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class RootFastcgiRecoverySafetyContractTest extends TestCase {
 public function testRecoveryIsExplicitlyGuarded(): void {
  $s=file_get_contents(dirname(__DIR__,2).'/scripts/ezs_supervisor_tick.ps1');
  self::assertIsString($s);
  foreach (['ROOT_RECOVERY_REFUSED_DESIRED_STATE_MISSING','ezs.desired-services.v1',
   'ROOT_RECOVERY_REFUSED_IDENTITY_AMBIGUOUS','ROOT_RECOVERY_REFUSED_LISTENER_NETSTAT',
   'ROOT_RECOVERY_REFUSED_SECOND_NETSTAT','ROOT_RECOVERY_BACKOFF',
   'ROOT_RECOVERY_REFUSED_REATTESTATION','ROOT_RECOVERY_STOP_CONFIRMED_PID',
   'ROOT_RECOVERY_STOPPED_NEXT_TICK_BOOT','CADDY_DEV_HTTP_TIMEOUT_OWNED_PROCESS_NO_STOP_SECONDS'] as $token)
   self::assertStringContainsString($token,$s);
  self::assertStringContainsString("Name='prod'",$s);
 }
}
