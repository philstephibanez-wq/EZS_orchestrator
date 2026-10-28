<?php
declare(strict_types=1);
$code=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['function HttpStatus','EZS_DEV_HTTP_CHECK port=','EZS_DEV_HTTP_TRANSPORT_FAILED_','status=$code','HttpStatus $port $path'] as $token){
 if(!str_contains($code,$token))throw new RuntimeException('DEV_HTTP_DIAG_MISSING:'.$token);
}
if(!str_contains($code,"throw 'EZS_DEV_APP_HTTP_NOT_READY'"))throw new RuntimeException('DEV_HTTP_FAIL_CLOSED_MISSING');
echo "EZS_DEV_HTTP_STATUS_DIAGNOSTICS_2_B4_OK\n";
