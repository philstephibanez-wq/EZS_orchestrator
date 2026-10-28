<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/AssistantReadinessProbe.php';
use Ezs\Web\Module\Coordination\AssistantReadinessProbe;
if(trim((string)file_get_contents(dirname(__DIR__).'/VERSION'))!=='4.2c13')throw new RuntimeException('VERSION');
$calls=[];
$p=new AssistantReadinessProbe(function(string $url)use(&$calls):string {
    $calls[]=$url;
    if($url==='http://127.0.0.1:8712/api/health')return '{"ok":true,"service":"EZStudioLab Assistant"}';
    if($url==='http://127.0.0.1:8712/api/inference/status')return '{"ok":true,"state":"READY"}';
    throw new RuntimeException('unexpected endpoint');
});
$s=$p->status();
if(!$s['web']||!$s['inference']||$s['dispatch_verified']||count($calls)!==2)throw new RuntimeException('READINESS');
echo "EZS_ASSISTANT_READINESS_4_2C13_OK\n";
