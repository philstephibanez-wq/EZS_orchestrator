<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
foreach(['if ($pidValue -eq 0) { continue }','if ($pidValue -lt 0)','EZS_V2_STOPPED_CADDY_PRESERVED'] as $term) {
    if (!str_contains($s,$term)) { throw new RuntimeException('missing '.$term); }
}
if(str_contains($s,"@('caddy','caddy_pid')")){throw new RuntimeException('shared Caddy must not be stopped');}
echo "CADDY_DEV_STOP_ZERO_PID_CONTRACT_OK\n";
