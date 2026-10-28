<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c12')throw new RuntimeException('VERSION');
require $root.'/src/Module/Coordination/LabQueueProbe.php';
use Ezs\Web\Module\Coordination\LabQueueProbe;
$previous=getenv('EZS_LAB_ANALYSIS_TOKEN');
$isolatedRoot=sys_get_temp_dir().'/ezs_lab_probe_'.bin2hex(random_bytes(6));
mkdir($isolatedRoot,0700,true);
try {
    putenv('EZS_LAB_ANALYSIS_TOKEN');
    $count=0;
    $probe=new LabQueueProbe(function()use(&$count){$count++;throw new RuntimeException('must_not_fetch');},$isolatedRoot);
    if($probe->status()['reason']!=='token_not_configured'||$count!==0)throw new RuntimeException('FAIL_CLOSED');
    putenv('EZS_LAB_ANALYSIS_TOKEN=synthetic-test-token');
    $probe=new LabQueueProbe(function(string $url,array $headers)use(&$count){
        $count++;
        if($url!=='http://127.0.0.1:8702/internal/analysis/desktop/jobs/queue')throw new RuntimeException('WRONG_ENDPOINT');
        if(!in_array('X-EZScore-Analysis-Token: synthetic-test-token',$headers,true))throw new RuntimeException('MISSING_TOKEN');
        return json_encode(['schema_version'=>'ezstudio.analysis-desktop.v1','jobs'=>[['id'=>181,'kind'=>'profile','status'=>'queued','priority'=>50]]]);
    },$isolatedRoot);
    $result=$probe->status();
    if(!$result['connected']||$result['jobs'][0]['id']!==181||$count!==1)throw new RuntimeException('READ_ONLY_FAILED');
    $bad=new LabQueueProbe(static fn()=>'{invalid',$isolatedRoot);
    if($bad->status()['connected'])throw new RuntimeException('INVALID_ACCEPTED');
    echo "EZS_LAB_QUEUE_READONLY_4_2C10_OK\n";
}finally{
    if($previous===false)putenv('EZS_LAB_ANALYSIS_TOKEN');else putenv('EZS_LAB_ANALYSIS_TOKEN='.$previous);
    @rmdir($isolatedRoot);
}
