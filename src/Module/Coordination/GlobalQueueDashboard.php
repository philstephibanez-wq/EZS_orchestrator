<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Coordination;

use PDO;

/** Canonical global-queue read model: never initializes or changes SQLite. */
final class GlobalQueueDashboard
{
    public static function read(?string $path=null):array
    {
        $path??=GlobalQueueLocation::path();
        if(!is_file($path))return ['available'=>false,'reason'=>'queue_database_missing','jobs'=>[]];
        try{
            $uri='file:'.str_replace(['%','?','#'],['%25','%3F','%23'],str_replace('\\','/',$path)).'?mode=ro';
            $db=new PDO('sqlite:'.$uri,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_TIMEOUT=>2]);
            $db->exec('PRAGMA query_only=ON');
            $sql="SELECT j.id,j.producer,j.external_id,j.kind,j.priority,j.resource_class,j.state,j.updated_at,
                  (SELECT e.progress_percent FROM global_queue_events e
                   WHERE e.job_id=j.id AND e.progress_percent IS NOT NULL ORDER BY e.event_id DESC LIMIT 1) AS progress_percent,
                  (SELECT e.phase FROM global_queue_events e
                   WHERE e.job_id=j.id ORDER BY e.event_id DESC LIMIT 1) AS phase
                  FROM global_queue_jobs j
                  ORDER BY CASE j.state WHEN 'running' THEN 0 WHEN 'queued' THEN 1 ELSE 2 END,
                  j.priority DESC,j.created_at ASC,j.id ASC LIMIT 100";
            $rows=$db->query($sql)->fetchAll(PDO::FETCH_ASSOC);
            return ['available'=>true,'reason'=>null,'jobs'=>$rows];
        }catch(\Throwable){
            return ['available'=>false,'reason'=>'queue_read_unavailable','jobs'=>[]];
        }
    }
}
