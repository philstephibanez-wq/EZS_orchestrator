<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/DevBackendOwnership.php';
use Ezs\Web\Module\Infrastructure\DevBackendOwnership as D;
$good=['ProcessId'=>4242,'ExecutablePath'=>'H:\\PHP\\php-8.5-x64\\php.exe','CommandLine'=>'"H:\\PHP\\php-8.5-x64\\php.exe" -S 127.0.0.1:8602 -t "H:\\EZScore_dev\\public"'];
if (D::classify(4242,$good)!=='legacy_exact') throw new RuntimeException('exact');
foreach ([
  ['ProcessId'=>4243] + $good,
  array_replace($good,['ExecutablePath'=>'H:\\evil\\php.exe']),
  array_replace($good,['CommandLine'=>'php -S 127.0.0.1:86020 -t H:\\EZScore_dev\\public']),
  array_replace($good,['CommandLine'=>'php -S 127.0.0.1:8602 -t H:\\EZScore']),
] as $bad) {
 if (D::classify(4242,$bad)!=='foreign') throw new RuntimeException('foreign_not_rejected');
}
$state=(new D())->snapshot();
if ($state['port']!==8602 || !in_array($state['ownership'],['absent','unknown','foreign','legacy_exact'],true)) throw new RuntimeException('snapshot');
echo "DEV_BACKEND_IDENTITY_OK\n";
