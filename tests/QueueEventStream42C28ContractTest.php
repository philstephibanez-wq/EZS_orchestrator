<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/QueueEventStream.php';
use Ezs\Web\Module\Coordination\QueueEventStream;
if(!preg_match('/^4\\.2c(\\d+)$/',trim((string)file_get_contents(dirname(__DIR__).'/VERSION')),$version)||(int)$version[1]<28)throw new RuntimeException('VERSION');
$s=QueueEventStream::encode([['event_id'=>17,'job_id'=>9,'event_type'=>'progress','progress_percent'=>42,'phase'=>'analyse']]);
if(!str_contains($s,"id: 17\n")||!str_contains($s,"event: queue.progress\n")||!str_contains($s,'"progress_percent":42'))throw new RuntimeException('SSE');
if(str_contains($s,'lease_token'))throw new RuntimeException('SECRET');
if(!str_starts_with(QueueEventStream::encode([]),"retry: 3000\n\n"))throw new RuntimeException('EMPTY');
echo "EZS_QUEUE_SSE_ONESHOT_4_2C28_OK\n";
