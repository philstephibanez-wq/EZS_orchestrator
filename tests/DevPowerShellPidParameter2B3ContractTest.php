<?php
declare(strict_types=1);
$root=dirname(__DIR__);
foreach(['start.ps1'=>'WaitOwned','stop.ps1'=>'Owned'] as $filename=>$function){
 $code=(string)file_get_contents($root.'/scripts/'.$filename);
 if(!str_contains($code,'function '.$function.'([int]$port,[int]$processId'))throw new RuntimeException('PROCESS_ID_PARAMETER_MISSING:'.$filename);
 if(preg_match('/\$pid\b/i',$code))throw new RuntimeException('POWERSHELL_RESERVED_PID_VARIABLE:'.$filename);
}
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
if(!str_contains($start,'EZS_DEV_APPS_READY_8502_8852')||!str_contains($stop,'EZS_STOP_PROD_MAINTENANCE_CONFIRMED'))throw new RuntimeException('LIFECYCLE_REGRESSION');
echo "EZS_DEV_POWERSHELL_PID_PARAMETER_2_B3_OK\n";
