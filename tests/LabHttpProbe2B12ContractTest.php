<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=(string)file_get_contents($r.'/src/Module/Infrastructure/DevHttpStatus.php');
$j=(string)file_get_contents($r.'/public/assets/ezs-infrastructure.js');
foreach(["'port'=>8702","'port'=>8701","\$target['kind'] === 'backend'","stream_set_timeout(\$socket,1,500000)","'http_status'=>null"] as $needle) {
    if(!str_contains($s,$needle))throw new RuntimeException('PROBE_REGRESSION:'.$needle);
}
if(str_contains($s,'stream_set_timeout($socket,0,700000)'))throw new RuntimeException('OLD_TIMEOUT');
if(!str_contains($j,'timeout:9000')||!str_contains($j,'FastCGI TCP ouvert'))throw new RuntimeException('UI_REGRESSION');
foreach([200,302,404,503] as $code) {
    $line="HTTP/1.1 $code Found";
    if(!preg_match('~^HTTP/1\.[01] ([1-5][0-9]{2})\b~',$line,$m)||(int)$m[1]!==$code)throw new RuntimeException('STATUS_PARSE:'.$code);
}
echo "EZS_LAB_HTTP_PROBE_2_B12_CONTRACT_OK\n";
