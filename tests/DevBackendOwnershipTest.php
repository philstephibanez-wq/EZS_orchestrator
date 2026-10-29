<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/src/Module/Infrastructure/DevBackendOwnership.php';
use Ezs\Web\Module\Infrastructure\DevBackendOwnership as Subject;

function same(string $expected, string $actual, string $case): void {
    if ($expected !== $actual) {
        throw new RuntimeException($case . ': attendu ' . $expected . ', obtenu ' . $actual);
    }
}
$valid = [
    'ProcessId' => 1234,
    'ExecutablePath' => 'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
    'CommandLine' => '"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8602',
];
same('owned_signature', Subject::classify(1234, $valid), 'identité exacte');
same('unknown', Subject::classify(0, $valid), 'pid 0');
same('foreign', Subject::classify(5678, $valid), 'pid différent');
$wrong = $valid;
$wrong['CommandLine'] = 'php-cgi.exe -b 127.0.0.1:86020';
same('foreign', Subject::classify(1234, $wrong), 'port préfixe');
$wrong['CommandLine'] = 'php-cgi.exe -b 127.0.0.1:8602';
$wrong['ExecutablePath'] = 'C:\\unrelated\\php-cgi.exe';
same('foreign', Subject::classify(1234, $wrong), 'exécutable étranger');
if (Subject::processByPid(0) !== null) throw new RuntimeException('PID nul non rejeté');
$source = (string) file_get_contents(dirname(__DIR__) . '/src/Module/Infrastructure/DevBackendOwnership.php');
foreach (['powershell.exe', 'cmd.exe', 'legacy_exact'] as $forbidden) {
    if (stripos($source, $forbidden) !== false) throw new RuntimeException('Source non conforme');
}
echo "EZS_DEV_BACKEND_OWNERSHIP_TEST_OK\n";
