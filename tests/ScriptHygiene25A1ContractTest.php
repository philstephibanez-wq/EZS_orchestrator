<?php
declare(strict_types=1);
$r=dirname(__DIR__);
foreach (['scripts/caddy-dev-lab-assistant-cutover.ps1','tests/CaddyLabAssistantCutover2B9ContractTest.php','tests/CaddyLabMediaResolution2B10ContractTest.php'] as $path) {
 if(is_file($r.'/'.$path))throw new RuntimeException('OBSOLETE_FILE_PRESENT:'.$path);
}
foreach (['scripts/start.ps1','scripts/stop.ps1','scripts/v2_lifecycle.ps1','scripts/lab-assistant.ps1','scripts/prod_lifecycle.ps1'] as $path) {
 if(!is_file($r.'/'.$path))throw new RuntimeException('ACTIVE_OR_UNREVIEWED_FILE_MISSING:'.$path);
}
$start=(string)file_get_contents($r.'/scripts/start.ps1');
$stop=(string)file_get_contents($r.'/scripts/stop.ps1');
foreach (['v2_lifecycle.ps1','lab-assistant.ps1'] as $p){
 if(!str_contains($start,$p)||!str_contains($stop,$p))throw new RuntimeException('LIFECYCLE_REFERENCE_MISSING:'.$p);
}
echo "EZS_SCRIPT_HYGIENE_2_5A1_CONTRACT_OK\n";
