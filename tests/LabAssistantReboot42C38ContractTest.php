<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=file_get_contents($r.'/scripts/start.ps1');
foreach(['EZS_LA_STALE_STATE_AFTER_REBOOT_CLEARED','EZS_LA_STALE_STATE_DETECTED_READ_ONLY','EZS_LA_STALE_OR_FOREIGN_STATE','Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$entry.pid)"','@(Listener $t.port).Count -gt 0'] as $part){if(!str_contains($s,$part))throw new RuntimeException('MISSING:'.$part);}
echo "EZS_LA_REBOOT_4_2C38_OK\n";
