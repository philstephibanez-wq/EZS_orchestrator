<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/Module/Infrastructure/EcosystemLifecycleGuard.php';
use Ezs\Web\Module\Infrastructure\EcosystemLifecycleGuard as Guard;
$state = ['php_pid'=>6340, 'started_utc'=>'2026-10-29T14:12:26Z'];
$live = ['pid'=>6340,'created'=>'20261029141215.000000+000',
    'executable'=>'H:\\PHP\\php-8.5-x64\\php-cgi.exe',
    'command'=>'"H:\\PHP\\php-8.5-x64\\php-cgi.exe" -b 127.0.0.1:8791'];
$check = static function(string $expected, array $a, array $b): void {
    $got = Guard::attestRootFastcgi($a,$b);
    if ($got !== $expected) throw new RuntimeException("Expected $expected got $got");
};
$check('creation_unattested',$state,$live);
$attested=$state; $attested['php_created_wmi']=$live['created'];
$check('identity_attested',$attested,$live);
$x=$live;$x['pid']=999;$check('pid_mismatch',$attested,$x);
$x=$live;$x['command']='php-cgi.exe -b 127.0.0.1:87910';$check('command_mismatch',$attested,$x);
$x=$live;$x['executable']='C:\\PHP\\php-cgi.exe';$check('executable_mismatch',$attested,$x);
$x=$live;$x['created']='20261029141216.000000+000';$check('creation_unattested',$attested,$x);
echo "EZS_TEST_003_OK\n";
