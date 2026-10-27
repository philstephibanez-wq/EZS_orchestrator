<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
$registration=strpos($s, '$registered = $true');
$probe=strpos($s, '$response = Invoke-WebRequest', $registration);
if($registration===false||$probe===false||$probe<=$registration)throw new RuntimeException('probe before metadata');
foreach(['EZS_V2_BACKEND_RETAINED_HTTP_NOT_READY','EZS_V2_STARTED_BACKEND_HTTP_DEGRADED','if (-not $registered -and'] as $key) if(!str_contains($s,$key))throw new RuntimeException('missing '.$key);
echo "EZS_V2_START_HTTP_DEGRADED_CONTRACT_OK\n";
