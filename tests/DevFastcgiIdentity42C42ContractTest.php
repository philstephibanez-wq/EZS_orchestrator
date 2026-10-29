<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
foreach(['function Dev-Identity','function Dev-TcpReachable','Dev-Identity 8602 $state.dev_pid $state.dev_created','Dev-Identity 8862 $state.preview_pid $state.preview_created','Dev-TcpReachable $port','if($RefreshDevApps){','if(-not(IsOwned $target.port $target.processId $target.stamp))'] as $part){
if(!str_contains($s,$part))throw new RuntimeException('MISSING:'.$part);
}
echo "EZS_DEV_FASTCGI_IDENTITY_4_2C42_OK\n";
