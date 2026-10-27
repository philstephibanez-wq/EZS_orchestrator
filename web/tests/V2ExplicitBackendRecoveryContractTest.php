<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
$section=substr($s,strpos($s,"if (\$Action -eq 'recover')"),strpos($s,"if (\$Action -eq 'status')")-strpos($s,"if (\$Action -eq 'recover')"));
foreach(['$ConfirmRecovery','$ExpectedPid','RECOVERY_REQUIRES_STOPPED_METADATA','RECOVERY_CADDY_IDENTITY_MISMATCH','RECOVERY_BACKEND_IDENTITY_MISMATCH','RECOVERY_COMMANDLINE_NOT_EXACT','RECOVERY_PID_CHANGED','operator_explicit_pid','EZS_V2_RECOVERED'] as $x) if(!str_contains($section,$x)) throw new RuntimeException('missing '.$x);
if(str_contains($section,'Stop-Process')||str_contains($section,'Start-Process')) throw new RuntimeException('recovery must not manage processes');
echo "EZS_V2_EXPLICIT_RECOVERY_CONTRACT_OK\n";
