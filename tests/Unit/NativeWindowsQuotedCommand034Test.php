<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use PHPUnit\Framework\TestCase;

final class NativeWindowsQuotedCommand034Test extends TestCase
{
    public function testPhpCgiQuotedArgumentsAndLegacyUnquotedAccepted(): void
    {
        $spec=NativeWindowsLifecycle::specs()['root_php'];
        $record=['pid'=>20260,'created'=>'20261030010611.000000+060'];
        $base=['pid'=>20260,'created'=>$record['created'],'executable'=>$spec['exe']];
        $port=[8791=>[20260]];
        self::assertTrue(NativeWindowsLifecycle::attest($record,$spec,[...$base,
            'command'=>'"H:\\PHP\\php-8.5-x64\\php-cgi.exe" "-b" "127.0.0.1:8791"'], $port));
        self::assertTrue(NativeWindowsLifecycle::attest($record,$spec,[...$base,
            'command'=>'"'.$spec['exe'].'" -b 127.0.0.1:8791'], $port));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$base,
            'command'=>'"'.$spec['exe'].'" "-b" "127.0.0.1:8791"'], [8791=>[]]));
    }

    public function testAttestationRejectsExtraMissingAndSpoofedArguments(): void
    {
        $spec=NativeWindowsLifecycle::specs()['root_php'];
        $record=['pid'=>42,'created'=>'20261030010611.000000+060'];
        $base=['pid'=>42,'created'=>$record['created'],'executable'=>$spec['exe']];
        foreach([
            '"'.$spec['exe'].'" "-b" "127.0.0.1:87910"',
            '"'.$spec['exe'].'" "-b" "127.0.0.1:8791" --other',
            '"'.$spec['exe'].'" "127.0.0.1:8791"',
            '"C:\\foreign\\php-cgi.exe" "-b" "127.0.0.1:8791"',
            '"'.$spec['exe'].'" "-b" "127.0.0.1:8791" "-b" "127.0.0.1:8791"',
            '"'.$spec['exe'].'" "-b 127.0.0.1:8791"',
        ] as $command) {
            self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$base,'command'=>$command],[8791=>[42]]),$command);
        }
    }

    public function testCaddyQuotedIndividualArgumentsAcceptedWithoutWeakeningPortCheck(): void
    {
        $spec=NativeWindowsLifecycle::specs()['root_caddy'];
        $record=['pid'=>91,'created'=>'20261030010611.000000+060'];
        $base=['pid'=>91,'created'=>$record['created'],'executable'=>$spec['exe']];
        $command='"H:\\Caddy\\caddy.exe" "run" "--config" "H:\\EZS_orchestrator\\config\\caddy\\Caddyfile.dev-lab-assistant-candidate" "--adapter" "caddyfile"';
        self::assertTrue(NativeWindowsLifecycle::attest($record,$spec,[...$base,'command'=>$command],[8790=>[91]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$spec,[...$base,'command'=>$command],[8790=>[]]));
    }
}
