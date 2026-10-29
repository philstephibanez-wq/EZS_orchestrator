<?php
declare(strict_types=1);
$r=dirname(__DIR__);
require $r.'/src/Module/Coordination/GlobalQueueStore.php';
require $r.'/src/Module/Coordination/GlobalQueueLocation.php';
require $r.'/src/Module/Coordination/GlobalQueueDashboard.php';
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use Ezs\Web\Module\Coordination\GlobalQueueDashboard;
if(trim(file_get_contents($r.'/VERSION'))!=='4.2c32')throw new RuntimeException('VERSION');
$f=sys_get_temp_dir().'/ezs_dashboard_'.bin2hex(random_bytes(8)).'.sqlite';
try{
 $q=new GlobalQueueStore($f);
 $a=$q->enqueue('lab','synthetic-1','dashboard-synthetic-lab','profile','cpu',50);
 $q->enqueue('assistant','synthetic-2','dashboard-synthetic-assistant','expertise','gpu',60);
 $claim=$q->claim('cpu');
 $q->heartbeat((int)$claim['id'],$claim['lease_token'],120,45,'analyse','Progression');
 $d=GlobalQueueDashboard::read($f);
 if(!$d['available']||count($d['jobs'])!==2)throw new RuntimeException('GLOBAL_READ');
 $lab=array_values(array_filter($d['jobs'],fn($x)=>$x['producer']==='lab'));
 if(count($lab)!==1||$lab[0]['progress_percent']!=45||$lab[0]['phase']!=='analyse')throw new RuntimeException('PROGRESS');
 if(GlobalQueueDashboard::read($f.'.missing')['available'])throw new RuntimeException('MISSING_DB');
 $controller=file_get_contents($r.'/src/Module/Coordination/Controller/JobsPageController.php');
 $twig=file_get_contents($r.'/templates/jobs/index.html.twig');
 if(str_contains($controller,'LabQueueProbe')||str_contains($controller,'GlobalQueueSnapshot')||str_contains($twig,'lab_queue')||str_contains($twig,'sonde LAB'))throw new RuntimeException('LEGACY_QUEUE_IN_UI');
 if(!str_contains($controller,'GlobalQueueDashboard::read()'))throw new RuntimeException('NOT_CANONICAL');
 echo "EZS_GLOBAL_QUEUE_DASHBOARD_4_2C32_OK\n";
}finally{unset($q);foreach([$f,$f.'-wal',$f.'-shm'] as $p)@unlink($p);}
