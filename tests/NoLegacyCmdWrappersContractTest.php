<?php
declare(strict_types=1);
$root=dirname(__DIR__);
foreach (['start.cmd','stop.cmd','status.cmd'] as $file) {
 if (is_file($root.'/scripts/'.$file)) throw new RuntimeException('LEGACY_CMD_WRAPPER_PRESENT:'.$file);
}
foreach (['start.ps1','stop.ps1','v2_lifecycle.ps1','prod_lifecycle.ps1'] as $file) {
 if (!is_file($root.'/scripts/'.$file)) throw new RuntimeException('ACTIVE_LIFECYCLE_FILE_MISSING:'.$file);
}
if(!is_file($root.'/runtime_components/prod_gateway/server.py')) throw new RuntimeException('ACTIVE_PROD_GATEWAY_MISSING');
echo "EZS_NO_LEGACY_CMD_WRAPPERS_OK\n";
