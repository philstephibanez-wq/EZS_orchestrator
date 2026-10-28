<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Coordination;

/** Read-only view of V1 result.json snapshots; never consumes the queue. */
final class LegacyJobHistoryReader
{
    public function __construct(private readonly string $root) {}
    public function recent(int $limit = 40): array
    {
        $limit=max(1,min(100,$limit));
        $rows=[];
        foreach (['dev','prod','lab'] as $target) {
            $dir=rtrim($this->root,'/\\').'/runtime/jobs/'.$target;
            if(!is_dir($dir))continue;
            foreach(new \DirectoryIterator($dir) as $job) {
                if($job->isDot()||!$job->isDir()||$job->isLink())continue;
                foreach(new \DirectoryIterator($job->getPathname()) as $run) {
                    if($run->isDot()||!$run->isDir()||$run->isLink())continue;
                    $path=$run->getPathname().'/result.json';
                    if(!is_file($path)||is_link($path)||filesize($path)>1048576)continue;
                    $raw=@file_get_contents($path);
                    if($raw===false)continue;
                    $data=json_decode($raw,true);
                    if(!is_array($data)||array_is_list($data))continue;
                    $id=filter_var($data['job_id']??$job->getFilename(),FILTER_VALIDATE_INT,['options'=>['min_range'=>1]]);
                    if($id===false)continue;
                    $state=strtolower((string)($data['state']??$data['status']??''));
                    $aliases=['success'=>'completed','succeeded'=>'completed','done'=>'completed','complete'=>'completed','error'=>'failed','failure'=>'failed'];
                    $state=$aliases[$state]??$state;
                    if(!in_array($state,['queued','running','completed','failed','finalize_error'],true))continue;
                    $rc=$data['analysis_returncode']??$data['returncode']??$data['return_code']??null;
                    if($rc!==null&&!is_int($rc))$rc=null;
                    $final=(string)($data['finalize_status']??'');
                    $rows[]=['job_id'=>(int)$id,'target'=>$target,'kind'=>substr((string)($data['kind']??'-'),0,80),'song_id'=>is_int($data['song_id']??null)?$data['song_id']:null,'song_title'=>substr((string)($data['song_title']??$data['title']??''),0,100),'state'=>$state,'analysis_returncode'=>$rc,'finalize_status'=>substr($final,0,40),'error'=>in_array($state,['failed','finalize_error'],true)?substr((string)($data['error']??''),0,240):null,'run'=>substr($run->getFilename(),0,100),'timestamp'=>gmdate('c',filemtime($path)?:0),'mtime'=>filemtime($path)?:0];
                }
            }
        }
        usort($rows,static fn(array $a,array $b):int=>$b['mtime']<=>$a['mtime']);
        return array_map(static function(array $row):array{unset($row['mtime']);return $row;},array_slice($rows,0,$limit));
    }
}
