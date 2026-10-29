<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$source=(string)file_get_contents($root.'/scripts/start.ps1');
$start=strpos($source,'function Invoke-EzsProdLifecycle {');
$end=strpos($source,'EZS_PROD_STOP_OWNED_OK',$start === false ? 0 : $start);
if($start===false||$end===false)throw new RuntimeException('PROD_HELPER_NOT_FOUND');
$prod=substr($source,$start,$end-$start);
foreach([
 'EZS_PROD_FASTCGI_4_2C50',
 'RedirectStandardError',
 'RedirectStandardOutput',
 'EZS_PROD_START_ATTESTATION_FAILED',
 'process_alive=',
 'identity_verified=',
 'listener_count=',
 'tcp_reachable=',
 'EZS_PROD_START_FAILED_',
 'EZS_PROD_START_MAINTENANCE_OK',
 'EZS_PROD_STALE_STATE_AFTER_REBOOT_CLEARED',
 'EZS_PROD_STOP_OWNED_OK'
] as $needle){
 if(!str_contains($source,$needle))throw new RuntimeException('MISSING:'.$needle);
}
foreach(['python.exe','server.py','prod_gateway\\server.py'] as $forbidden){
 if(str_contains($prod,$forbidden))throw new RuntimeException('FORBIDDEN_PYTHON:'.$forbidden);
}
if(!str_contains($prod,'[array]::Reverse($started)')||!str_contains($prod,'Stop-Process -Id $entry.pid')){
 throw new RuntimeException('ROLLBACK_MISSING');
}
echo "EZS_PROD_FASTCGI_DIAG_4_2C50_OK\n";
