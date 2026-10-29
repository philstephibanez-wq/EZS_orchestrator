<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['EZS_START_SHARED_CADDY_IDENTITY_VERIFIED_PRESERVED','EZS_DEV_ALREADY_RUNNING_IDENTITY_VERIFIED','Tcp-Reachable 8791','OwnedDevCaddy $savedCaddyId','if ($phpId -ne 0 -and $null -ne (ProcessInfo $phpId))','EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED'] as $v){if(!str_contains($s,$v))throw new RuntimeException('MISSING:'.$v);}
if(str_contains($s,'$edgeHealthy = Wait-SharedCaddyAttestation $caddyId'))throw new RuntimeException('SOCKET_GATING_START');
echo "EZS_START_RECONCILE_4_2C41_OK\n";
