<?php
declare(strict_types=1);
$src=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
$begin=strpos($src,"    if (\$Action -eq 'recover') {");
$end=strpos($src,"    if (\$Action -eq 'status') {");
if ($begin===false || $end===false || $end<=$begin) throw new RuntimeException('recovery boundary');
$recovery=substr($src,$begin,$end-$begin);
foreach (['RECOVERY_REQUIRES_STOPPED_METADATA','RECOVERY_CADDY_IDENTITY_MISMATCH','RECOVERY_BACKEND_IDENTITY_MISMATCH','RECOVERY_COMMANDLINE_NOT_EXACT','RECOVERY_PID_CHANGED','operator_explicit_pid','EZS_V2_RECOVERED'] as $item){
    if (!str_contains($recovery,$item)) throw new RuntimeException('missing '.$item);
}
if (str_contains($recovery,'Stop-Process') || str_contains($recovery,'Start-Process')) throw new RuntimeException('recovery must not manage processes');
if (substr_count($src,"if (\$Action -eq 'status')")!==1) throw new RuntimeException('duplicate code');
echo "EZS_V2_EXPLICIT_RECOVERY_CONTRACT_OK\n";
