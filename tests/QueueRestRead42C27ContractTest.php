<?php
declare(strict_types=1);
$r=dirname(__DIR__);
require $r.'/src/Module/Coordination/GlobalQueueStore.php';
require $r.'/src/Module/Coordination/QueueRestReadModel.php';
require $r.'/src/Module/Coordination/QueueRestAccess.php';
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\QueueRestReadModel;
use Ezs\Web\Module\Coordination\QueueRestAccess;
if(!preg_match('/^4\\.2c(\\d+)$/',trim((string)file_get_contents($r.'/VERSION')),$version)|| (int)$version[1]<27)throw new RuntimeException('VERSION');
$a=str_repeat('A',48);$b=str_repeat('B',48);
if(QueueRestAccess::producerFor('Bearer '.$a,['lab'=>$a,'assistant'=>$b])!=='lab')throw new RuntimeException('AUTH');
if(QueueRestAccess::producerFor('Bearer '.$a,['lab'=>$a,'assistant'=>$a])!==null)throw new RuntimeException('TOKEN_COLLISION');
if(QueueRestAccess::producerFor('Bearer '.str_repeat('C',48),['lab'=>$a])!==null)throw new RuntimeException('FAIL_CLOSED');
$f=sys_get_temp_dir().'/ezs_rest_'.bin2hex(random_bytes(8)).'.sqlite';
try{
 $q=new GlobalQueueStore($f);
 $lab=$q->enqueue('lab','synth1','lab-rest-test','profile','cpu');
 $q->enqueue('assistant','synth2','assistant-rest-test','expertise','gpu');
 $owned=$q->claim('cpu');
 $q->heartbeat((int)$owned['id'],$owned['lease_token'],120,42,'analyse','Progression');
 $v=new QueueRestReadModel($f);
 if(count($v->jobs('lab'))!==1||count($v->jobs('assistant'))!==1)throw new RuntimeException('LIST_SCOPE');
 if($v->job('assistant',(int)$lab['id'])!==null)throw new RuntimeException('CROSS_SCOPE');
 if(count($v->events('lab',0))!==1||count($v->events('assistant',0))!==0)throw new RuntimeException('EVENT_SCOPE');
 if(str_contains(json_encode($v->jobs('lab')),'lease_token'))throw new RuntimeException('TOKEN_LEAK');
 echo "EZS_QUEUE_REST_READ_4_2C27_OK\n";
}finally{unset($q,$v);foreach([$f,$f.'-wal',$f.'-shm'] as $p)@unlink($p);}
