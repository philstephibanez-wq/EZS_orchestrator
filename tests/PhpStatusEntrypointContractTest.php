<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(is_file($root.'/scripts/status.cmd')) throw new RuntimeException('LEGACY_STATUS_CMD_STILL_PRESENT');
$php=(string)file_get_contents($root.'/bin/infrastructure.php');
foreach (['status','ezs.infrastructure.status.php.v1','state_present','listeners_ready'] as $marker) if(!str_contains($php,$marker)) throw new RuntimeException('PHP_STATUS_ENTRYPOINT_MISSING: '.$marker);
foreach(['start.ps1','stop.ps1','v2_lifecycle.ps1','prod_lifecycle.ps1'] as $file) if(!is_file($root.'/scripts/'.$file)) throw new RuntimeException('ACTIVE_PROCESS_LIFECYCLE_MISSING: '.$file);
echo "EZS_PHP_STATUS_ENTRYPOINT_CONTRACT_OK\n";
