<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['function Wait-SharedCaddyAttestation','OwnedDevCaddy $processId','Port-Owned 8702 $processId','Port-Owned 8712 $processId','EZS_SHARED_CADDY_LISTENER','EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED'] as $term) {
 if(!str_contains($s,$term))throw new RuntimeException('MISSING: '.$term);
}
if(substr_count($s,'Wait-SharedCaddyAttestation $savedCaddyId')!==1||substr_count($s,'Wait-SharedCaddyAttestation $caddyId')!==1)throw new RuntimeException('ATTESTATION_NOT_WIRED');
echo "EZS_SHARED_CADDY_ATTESTATION_4_2C39_OK\n";
