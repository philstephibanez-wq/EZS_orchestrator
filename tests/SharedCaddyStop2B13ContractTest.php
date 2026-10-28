<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach (['EZS_STOP_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED','EZS_START_ORCHESTRATOR_BACKEND_OK_SHARED_CADDY_PRESERVED','EZS_STOP_REFUSED_UNVERIFIED_SHARED_CADDY','EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED','$s.php_pid = 0'] as $needle) {
 if(!str_contains($s,$needle))throw new RuntimeException('SHARED_CADDY_STOP_MISSING:'.$needle);
}
$start=strpos($s,"if (\$Action -eq 'stop') {");
$end=strpos($s,'if ($null -ne $s) {',$start);
if($start===false||$end===false)throw new RuntimeException('STOP_BLOCK_MISSING');
$stop=substr($s,$start,$end-$start);
if(str_contains($stop,'Stop-Process -Id $c')||str_contains($stop,'Remove-Item -LiteralPath $stateFile'))throw new RuntimeException('SHARED_CADDY_MUST_SURVIVE_STOP');
echo "EZS_SHARED_CADDY_STOP_2_B13_CONTRACT_OK\n";
