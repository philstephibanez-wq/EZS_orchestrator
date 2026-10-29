<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/GlobalQueueStore.php';
use Ezs\Web\Module\Coordination\GlobalQueueStore;
if (!preg_match('/^4\\.2c(\\d+)$/',trim((string)file_get_contents(dirname(__DIR__).'/VERSION')),$v) || (int)$v[1] < 23) throw new RuntimeException('VERSION');
if (!extension_loaded('pdo_sqlite')) throw new RuntimeException('SQLITE_REQUIRED');
$path=sys_get_temp_dir().DIRECTORY_SEPARATOR.'ezs_global_queue_'.bin2hex(random_bytes(10)).'.sqlite';
function rejected(callable $f):void {try{$f();}catch(\DomainException|\InvalidArgumentException){return;}throw new RuntimeException('EXPECTED_REJECTION');}
try {
    $q=new GlobalQueueStore($path);
    $lab=$q->enqueue('LAB','193-synthetic','test-lab-193','analysis','gpu',60);
    $assistant=$q->enqueue('Assistant','review-synthetic','test-assistant-1','expertise','cpu',80);
    if($q->enqueue('LAB','193-synthetic','test-lab-193','analysis','gpu',60)['id']!==$lab['id'])throw new RuntimeException('NOT_IDEMPOTENT');
    rejected(fn()=>$q->enqueue('LAB','193-synthetic','test-lab-193','changed','gpu',60));
    rejected(fn()=>$q->enqueue('LAB','193-synthetic','different-key','analysis','gpu',60));
    $a=$q->claim('cpu');
    if($a['id']!==$assistant['id'] || $q->claim('cpu')!==null)throw new RuntimeException('CPU_CLAIM');
    $g=$q->claim('gpu');
    if($g['id']!==$lab['id'] || $q->claim('gpu')!==null)throw new RuntimeException('GPU_CLAIM');
    rejected(fn()=>$q->finish((int)$g['id'],str_repeat('a',64),true));
    $reopen=new GlobalQueueStore($path);
    if($reopen->byId((int)$g['id'])['state']!=='running')throw new RuntimeException('NOT_PERSISTED');
    if($reopen->finish((int)$g['id'],$g['lease_token'],true)['state']!=='completed')throw new RuntimeException('FINISH');
    rejected(fn()=>$reopen->finish((int)$g['id'],$g['lease_token'],true));
    if($reopen->finish((int)$a['id'],$a['lease_token'],false)['state']!=='failed')throw new RuntimeException('FAIL');
    echo "EZS_GLOBAL_QUEUE_PERSISTENCE_4_2C23_OK\n";
} finally {
    unset($reopen,$q);
    foreach([$path,$path.'-wal',$path.'-shm'] as $p)@unlink($p);
}
