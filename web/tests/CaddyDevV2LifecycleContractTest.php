<?php
$s=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
foreach(['caddy_dev_shared.ps1','EZS_V2_STOPPED_CADDY_PRESERVED','caddy_pid=$caddyPid'] as $term){if(!str_contains($s,$term))throw new RuntimeException($term);}
if(str_contains($s,"@('caddy','caddy_pid')")||str_contains($s, 'Stop-Process -Id $caddyPid' ))throw new RuntimeException('shared stop');
echo "CADDY_DEV_V2_LIFECYCLE_CONTRACT_OK\n";
