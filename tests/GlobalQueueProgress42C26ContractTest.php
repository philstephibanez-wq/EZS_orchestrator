<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/GlobalQueueStore.php';
use Ezs\Web\Module\Coordination\GlobalQueueStore;
function reject(callable $cb): void {try {$cb();} catch (\DomainException|\InvalidArgumentException) {return;} throw new RuntimeException('REJECTION_EXPECTED');}
$path=sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_progress_'.bin2hex(random_bytes(8)).'.sqlite';
try {
    $q=new GlobalQueueStore($path);
    $a=$q->enqueue('LAB','synthetic-progress','lab-progress-demo','analysis','cpu');
    $b=$q->enqueue('Assistant','synthetic-review','assistant-progress-demo','expertise','gpu');
    $lab=$q->claim('cpu');$assistant=$q->claim('gpu');
    $p=$q->heartbeat((int)$lab['id'],$lab['lease_token'],120,45,'profile','Processing');
    $q->heartbeat((int)$lab['id'],$lab['lease_token'],120,62,'profile','Processing');
    $q->heartbeat((int)$assistant['id'],$assistant['lease_token'],120,null,'review');
    if($p['progress_percent']!==45)throw new RuntimeException('PROGRESS');
    reject(fn()=>$q->heartbeat((int)$lab['id'],$lab['lease_token'],120,40));
    reject(fn()=>$q->heartbeat((int)$lab['id'],str_repeat('a',64),120,80));
    reject(fn()=>$q->heartbeat((int)$lab['id'],$lab['lease_token'],120,100));
    $fresh=new GlobalQueueStore($path);
    $labEvents=$fresh->events('LAB');
    $assistantEvents=$fresh->events('Assistant');
    if(count($labEvents)!==2||count($assistantEvents)!==1||$labEvents[1]['progress_percent']!=62)throw new RuntimeException('PERSISTED_EVENTS');
    if($fresh->events('Assistant',(int)$assistantEvents[0]['event_id'])!==[])throw new RuntimeException('CURSOR');
    if($fresh->finish((int)$lab['id'],$lab['lease_token'],true)['state']!=='completed')throw new RuntimeException('FINISH');
    reject(fn()=>$fresh->heartbeat((int)$lab['id'],$lab['lease_token'],120,90));
    echo "EZS_GLOBAL_QUEUE_PROGRESS_4_2C26_OK\n";
} finally {
    unset($q,$fresh);
    foreach([$path,$path.'-wal',$path.'-shm'] as $p)@unlink($p);
}
