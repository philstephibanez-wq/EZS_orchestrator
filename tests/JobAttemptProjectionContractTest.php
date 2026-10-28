<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/JobAttemptProjection.php';
use Ezs\Web\Module\Coordination\JobAttemptProjection as P;
function verify(string $name,array $data,string $expected):void {
    if(P::project($data)['state']!==$expected)throw new RuntimeException($name);
}
function reject(string $name,array $data):void {
    try{P::project($data);}catch(InvalidArgumentException|DomainException){return;}
    throw new RuntimeException('ACCEPTED_INVALID:'.$name);
}
$b=['job_id'=>15,'target'=>'dev'];
verify('queued',$b+['state'=>'queued'],'queued');
verify('running',$b+['state'=>'running','started_at'=>'2026-10-28T12:00:00Z'],'running');
verify('completed',$b+['state'=>'completed','analysis_returncode'=>0,'finalize_status'=>'ok'],'completed');
verify('finalize_error',$b+['state'=>'finalize_error','analysis_returncode'=>0,'finalize_status'=>'error'],'finalize_error');
verify('failed',$b+['state'=>'failed','analysis_returncode'=>1],'failed');
reject('no_false_failure',$b+['state'=>'failed','analysis_returncode'=>0,'finalize_status'=>'error']);
reject('no_false_success',$b+['state'=>'completed','analysis_returncode'=>0,'finalize_status'=>'error']);
reject('no_false_finalize_error',$b+['state'=>'finalize_error','analysis_returncode'=>1,'finalize_status'=>'error']);
reject('unknown_target',['job_id'=>2,'target'=>'other','state'=>'queued']);
reject('unknown_state',$b+['state'=>'cancelled']);
echo "EZS_JOB_ATTEMPT_PROJECTION_4_2C2_OK\n";
