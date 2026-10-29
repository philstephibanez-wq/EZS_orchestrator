<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/src/Module/Infrastructure/DevBackendOwnership.php';
use Ezs\Web\Module\Infrastructure\DevBackendOwnership as Subject;

$assert = static function (string $expected, string $actual, string $case): void {
    if ($expected !== $actual) {
        throw new RuntimeException($case . ': attendu ' . $expected . ', obtenu ' . $actual);
    }
};
$valid = [
    'ProcessId' => 1234,
    'ExecutablePath' => 'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
    'CommandLine' => '"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8602',
];
$assert('owned_signature', Subject::classify(1234, $valid), 'identite exacte');
$assert('unknown', Subject::classify(0, $valid), 'pid zero');
$assert('foreign', Subject::classify(5678, $valid), 'pid different');
$wrong = $valid;
$wrong['CommandLine'] = 'php-cgi.exe -b 127.0.0.1:86020';
$assert('foreign', Subject::classify(1234, $wrong), 'port prefixe');
$wrong['CommandLine'] = 'php-cgi.exe -b 127.0.0.1:8602';
$wrong['ExecutablePath'] = 'C:\\unrelated\\php-cgi.exe';
$assert('foreign', Subject::classify(1234, $wrong), 'executable etranger');
if (Subject::processByPid(0) !== null) {
    throw new RuntimeException('PID nul non rejete');
}
echo "EZS_TEST_001_OK\n";
