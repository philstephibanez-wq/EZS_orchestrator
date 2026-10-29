<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach (['function Port-Owned([int]$port, [int]$processId)','netstat -ano -p tcp','LISTENING','if ($listeners.Count -gt 0)','return ($owners.Count -eq 1 -and $owners[0] -eq $processId)'] as $term) {
 if (!str_contains($s,$term)) throw new RuntimeException('MISSING: '.$term);
}
echo "EZS_PORT_OWNERSHIP_NETSTAT_4_2C40_OK\n";
