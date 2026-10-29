<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\EcosystemLifecycleGuard;
use PHPUnit\Framework\TestCase;

final class RootFastcgiAttestation009Test extends TestCase
{
    public function testAttestationRejectsSessionTimestamp(): void
    {
        $live = self::live();
        self::assertSame('creation_unattested', EcosystemLifecycleGuard::attestRootFastcgi([
            'php_pid' => 6340,
            'started_utc' => '2026-10-29T14:12:26Z',
        ], $live));
    }

    public function testAttestationRequiresExactProcessIdentity(): void
    {
        $live = self::live();
        $state = ['php_pid' => 6340, 'php_created_wmi' => $live['created']];
        self::assertSame('identity_attested', EcosystemLifecycleGuard::attestRootFastcgi($state, $live));
        self::assertSame('pid_mismatch', EcosystemLifecycleGuard::attestRootFastcgi($state, [...$live, 'pid'=>123]));
        self::assertSame('command_mismatch', EcosystemLifecycleGuard::attestRootFastcgi($state, [...$live, 'command'=>'php-cgi.exe -b 127.0.0.1:87910']));
        self::assertSame('executable_mismatch', EcosystemLifecycleGuard::attestRootFastcgi($state, [...$live, 'executable'=>'C:\\wrong\\php-cgi.exe']));
        self::assertSame('creation_unattested', EcosystemLifecycleGuard::attestRootFastcgi($state, [...$live, 'created'=>'different']));
    }

    private static function live(): array
    {
        return [
            'pid'=>6340,
            'created'=>'20261029141215.000000+000',
            'executable'=>'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
            'command'=>'"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8791',
        ];
    }
}
