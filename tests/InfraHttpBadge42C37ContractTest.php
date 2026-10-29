<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$js=(string)file_get_contents($r.'/public/assets/ezs-infrastructure.js');
foreach(['code >= 200 && code < 400','code >= 400','httpError ? \'text-bg-danger\'','text-bg-warning text-bg-danger','HTTP opérationnel'] as $part){
 if(!str_contains($js,$part))throw new RuntimeException('MISSING_HTTP_STATE: '.$part);
}
if(str_contains($js,"item.http_status !== null ? 'text-bg-success'"))throw new RuntimeException('HTTP_ERRORS_GREEN');
echo "EZS_INFRA_HTTP_BADGE_4_2C37_OK\n";
