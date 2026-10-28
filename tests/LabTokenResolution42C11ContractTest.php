<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c12')throw new RuntimeException('VERSION');
require $root.'/src/Module/Coordination/LabQueueProbe.php';
use Ezs\Web\Module\Coordination\LabQueueProbe;
$old=getenv('EZS_LAB_ANALYSIS_TOKEN');
$dir=sys_get_temp_dir().'/ezs_lab_token_'.bin2hex(random_bytes(8));
mkdir($dir,0700,true);
$calls=0;
$transport=static function(string $url,array $headers)use(&$calls):string{
    $calls++;
    if($url!=='http://127.0.0.1:8702/internal/analysis/desktop/jobs/queue')throw new RuntimeException('UNEXPECTED_URL');
    $expected='X-EZScore-Analysis-Token: '.$GLOBALS['expectedToken'];
    if(!in_array($expected,$headers,true))throw new RuntimeException('TOKEN_NOT_MATCHED');
    return '{"schema_version":"ezstudio.analysis-desktop.v1","jobs":[]}';
};
try{
    putenv('EZS_LAB_ANALYSIS_TOKEN');
    $GLOBALS['expectedToken']='example-quoted';
    file_put_contents($dir.'/.env.local',"# comment\nEZSTUDIO_ANALYSIS_WORKER_TOKEN=\"example-quoted\"\n");
    $probe=new LabQueueProbe($transport,$dir);
    if(!$probe->status()['connected']||$calls!==1)throw new RuntimeException('LOCAL_TOKEN_FAILED');
    $GLOBALS['expectedToken']='explicit-example';
    putenv('EZS_LAB_ANALYSIS_TOKEN=explicit-example');
    if(!(new LabQueueProbe($transport,$dir))->status()['connected']||$calls!==2)throw new RuntimeException('EXPLICIT_PRIORITY');
    putenv('EZS_LAB_ANALYSIS_TOKEN');
    unlink($dir.'/.env.local');
    $missing=(new LabQueueProbe($transport,$dir))->status();
    if($missing['reason']!=='token_not_configured'||$calls!==2)throw new RuntimeException('FAIL_CLOSED');
    echo "EZS_LAB_TOKEN_RESOLUTION_4_2C11_OK\n";
}finally{
    unset($GLOBALS['expectedToken']);
    if($old===false)putenv('EZS_LAB_ANALYSIS_TOKEN');else putenv('EZS_LAB_ANALYSIS_TOKEN='.$old);
    @unlink($dir.'/.env.local');@rmdir($dir);
}
