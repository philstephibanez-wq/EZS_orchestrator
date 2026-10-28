<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/JobAttemptProjection.php';
require dirname(__DIR__).'/src/Module/Coordination/JobRegistry.php';
use Ezs\Web\Module\Coordination\JobRegistry;
function bad(callable $cb):void{try{$cb();}catch(DomainException|InvalidArgumentException){return;}throw new RuntimeException('EXPECTED_REJECTION');}
if(!extension_loaded('pdo_sqlite'))throw new RuntimeException('PDO_SQLITE_REQUIRED');
$path=sys_get_temp_dir().'/ezs_queue_42c3_'.bin2hex(random_bytes(8)).'.sqlite';
try{
 $r=new JobRegistry($path);
 $r->register('dev',12,'stems');$r->register('dev',12,'stems');
 bad(fn()=>$r->register('dev',12,'lyrics'));
 $b=['target'=>'dev','job_id'=>12];
 $r->recordAttempt($b+['state'=>'running','started_at'=>'2026-10-28T12:00:00Z'],1);
 $r->recordAttempt($b+['state'=>'running','started_at'=>'2026-10-28T12:00:00Z'],1);
 bad(fn()=>$r->recordAttempt($b+['state'=>'running'],2));
 $r->recordAttempt($b+['state'=>'finalize_error','analysis_returncode'=>0,'finalize_status'=>'error','started_at'=>'2026-10-28T12:00:00Z'],1);
 bad(fn()=>$r->recordAttempt($b+['state'=>'completed','analysis_returncode'=>0,'finalize_status'=>'ok'],1));
 $r->recordAttempt($b+['state'=>'running'],2);
 $r->recordAttempt($b+['state'=>'completed','analysis_returncode'=>0,'finalize_status'=>'ok'],2);
 $s=new JobRegistry($path);
 if($s->job('dev',12)['state']!=='completed'||$s->attempt('dev',12,1)['state']!=='finalize_error')throw new RuntimeException('PERSISTENCE_FAILED');
 echo "EZS_JOB_REGISTRY_4_2C3_OK\n";
} finally {
 unset($s,$r);
 foreach([$path,$path.'-wal',$path.'-shm'] as $f)@unlink($f);
}
