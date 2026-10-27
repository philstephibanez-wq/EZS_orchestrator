<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/DevHttpStatus.php';
$items=(new \Ezs\Web\Module\Infrastructure\DevHttpStatus())->snapshot();
if(count($items)!==4)throw new RuntimeException('targets');
$seen=[];
foreach($items as $item){
 if($item['port']===8501||$item['port']===8510||$item['port']===8511)throw new RuntimeException('prod_probe');
 if(!in_array($item['kind'],['backend','facade'],true))throw new RuntimeException('kind');
 if(!is_bool($item['tcp_listening'])||!is_bool($item['http_reachable']))throw new RuntimeException('types');
 $seen[]=$item['port'];
}
sort($seen);
if($seen!==[8502,8701,8702,8712])throw new RuntimeException('unexpected_ports');
echo "DEV_HTTP_STATUS_OK\n";
