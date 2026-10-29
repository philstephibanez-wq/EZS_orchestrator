<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\EcosystemStatusCommand;

final class EcosystemStatus013Test extends TestCase
{
    private function process(): array
    {
        return ['pid'=>6340, 'created'=>'20261029141215.000000+000',
            'executable'=>'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
            'command'=>'"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8791'];
    }
    public function testMissingStateIsNotMisrepresentedAsStopped(): void
    {
        self::assertSame('ABSENT_UNVERIFIED', EcosystemStatusCommand::devEvidence(null, []));
    }
    public function testHistoricalStateCannotAttestProcessWithoutCreationTimestamp(): void
    {
        self::assertSame('creation_unattested', EcosystemStatusCommand::devEvidence(['php_pid'=>6340], [$this->process()]));
    }
    public function testExactIdentityIsAttested(): void
    {
        $proc=$this->process();
        self::assertSame('identity_attested', EcosystemStatusCommand::devEvidence(['php_pid'=>6340,'php_created_wmi'=>$proc['created']], [$proc]));
    }
    public function testMissingRecordedProcessIsReported(): void
    {
        self::assertSame('RECORDED_PROCESS_NOT_FOUND', EcosystemStatusCommand::devEvidence(['php_pid'=>6340], []));
    }
    public function testReusedPidFailsAttestation(): void
    {
        $proc=$this->process(); $proc['created']='20261029141515.000000+000';
        self::assertSame('creation_unattested', EcosystemStatusCommand::devEvidence(['php_pid'=>6340,'php_created_wmi'=>'20261029141215.000000+000'], [$proc]));
    }
}
