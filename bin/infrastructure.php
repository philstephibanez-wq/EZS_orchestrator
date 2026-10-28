<?php
declare(strict_types=1);

// Lecture d'état et préflight natifs PHP. Aucune création/arrêt de processus.
$root=dirname(__DIR__);
$action=$argv[1]??'status';
if(!in_array($action,['status','preflight','fastcgi-incident','observe-fastcgi'],true)){fwrite(STDERR,"EZS_PHP_UNKNOWN_ACTION\n");exit(2);}
function fail(string $reason): never {fwrite(STDERR,$reason."\n");exit(1);}
function state(string $file): ?array {
    if(!is_file($file))return null;
    try {$v=json_decode((string)file_get_contents($file),true,512,JSON_THROW_ON_ERROR);}
    catch(Throwable){fail('EZS_PHP_INVALID_STATE:'.$file);}
    return is_array($v)?$v:null;
}
function port(int $number): bool {
    $e=0;$s='';$h=@stream_socket_client('tcp://127.0.0.1:'.$number,$e,$s,0.5);
    if(!is_resource($h))return false;
    fclose($h);return true;
}
if($action==='preflight'){
    foreach([
        $root.'/public/index.php',
        $root.'/vendor/autoload.php',
        $root.'/config/caddy/Caddyfile.dev-root-candidate',
        $root.'/config/caddy/Caddyfile.prod',
        $root.'/config/caddy/Caddyfile.prod-internal-candidate',
        'H:/EZScore/public/index.php',
    ] as $path){if(!is_file($path))fail('EZS_PHP_MISSING:'.$path);}
    foreach([
        $root.'/config/caddy/Caddyfile.dev-root-candidate',
        $root.'/config/caddy/Caddyfile.prod',
        $root.'/config/caddy/Caddyfile.prod-internal-candidate'
    ] as $path){
        $cmd=['H:/Caddy/caddy.exe','validate','--config',$path,'--adapter','caddyfile'];
        $p=proc_open($cmd,[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,$root);
        if(!is_resource($p))fail('EZS_PHP_CADDY_PREFLIGHT_LAUNCH_FAILED');
        fclose($pipes[0]);stream_get_contents($pipes[1]);fclose($pipes[1]);
        $error=stream_get_contents($pipes[2]);fclose($pipes[2]);
        if(proc_close($p)!==0)fail('EZS_PHP_CADDY_INVALID:'.basename($path).' '.trim($error));
    }
    echo "EZS_PHP_INFRA_PREFLIGHT_OK\n";exit(0);
}
require_once $root.'/src/Module/Infrastructure/WindowsPortOwnership.php';
if($action==='fastcgi-incident'){
 require_once $root.'/src/Module/Infrastructure/FastcgiIncidentReport.php';
 $devState=state($root.'/runtime/v2-dev/processes.json');
 echo json_encode(\Ezs\Web\Module\Infrastructure\FastcgiIncidentReport::collect($root,$devState),JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
 exit(0);
}
$dev=state($root.'/runtime/v2-dev/processes.json');
$prod=state($root.'/runtime/v2-prod/processes.json');
$devListen=port(8790)&&port(8791);
$prodListen=port(8501)&&port(8510)&&port(8511)&&port(8512);
$spec=[];
foreach([['dev_php',$dev,'php_pid',8791,'php-cgi.exe'],['dev_caddy',$dev,'caddy_pid',8790,'caddy.exe'],['prod_php',$prod,'php_pid',8512,'php-cgi.exe'],['prod_internal',$prod,'internal_pid',8511,'caddy.exe'],['prod_gateway',$prod,'gateway_pid',8510,'python.exe'],['prod_edge',$prod,'edge_pid',8501,'caddy.exe']] as [$name,$state,$key,$port,$image]) {
 if(is_array($state)&&isset($state[$key])&&is_numeric($state[$key]))$spec[$name]=[$port,(int)$state[$key],$image];
}
$ownership=\Ezs\Web\Module\Infrastructure\WindowsPortOwnership::snapshot($spec);
if($action==='observe-fastcgi'){
 require_once $root.'/src/Module/Infrastructure/FastcgiTransitionJournal.php';
 $check=$ownership['checks']['dev_php']??[];
 $observation=\Ezs\Web\Module\Infrastructure\FastcgiTransitionJournal::observe(
  rtrim(sys_get_temp_dir(),'\\/').'/ezs-orchestrator',
  isset($check['expected_pid'])?(int)$check['expected_pid']:null,
  $check['listener_pids']??[],
  $check['image']??null
 );
 echo json_encode($observation,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
 exit(0);
}
echo json_encode([
 'schema'=>'ezs.infrastructure.status.php.v1',
 'dev'=>['state_present'=>$dev!==null,'listeners_ready'=>$devListen,'ports'=>[8790,8791]],
 'prod'=>['state_present'=>$prod!==null,'listeners_ready'=>$prodListen,'ports'=>[8501,8510,8511,8512]],
 'ownership'=>$ownership,
 'warning'=>'Port/PID/image diagnostics only: full process identity remains unverified; never use this result to terminate processes'
],JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
