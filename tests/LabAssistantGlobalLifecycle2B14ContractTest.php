<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$la=(string)file_get_contents($r.'/scripts/start.ps1');
$stop=(string)file_get_contents($r.'/scripts/stop.ps1');
$start=(string)file_get_contents($r.'/scripts/start.ps1');
foreach (["ValidateSet('preflight','start','status','stop')","if(\$Action -eq 'stop')","EZS_LA_STOP_REFUSED_UNVERIFIED_OWNER_","EZS_LA_STOP_REFUSED_UNOWNED_PORT_","EZS_LA_BACKENDS_STOP_OK_8701_8713_SHARED_CADDY_PRESERVED","Remove-Item -LiteralPath \$statePath -Force"] as $s) {
 if(!str_contains($la,$s))throw new RuntimeException('LAB_ASSISTANT_STOP_MISSING:'.$s);
}
$laStop=strpos($stop,"'lab-assistant.ps1') -Action stop");
$orcStop=strpos($stop,"'v2_lifecycle.ps1') -Action stop");
if($laStop===false||$orcStop===false||$laStop>$orcStop)throw new RuntimeException('GLOBAL_STOP_ORDER');
if(substr_count($start,"'lab-assistant.ps1') -Action start")!==2)throw new RuntimeException('GLOBAL_START_INCOMPLETE');
echo "EZS_LA_GLOBAL_LIFECYCLE_2_B14_CONTRACT_OK\n";
