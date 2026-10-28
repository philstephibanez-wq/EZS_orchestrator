<?php
declare(strict_types=1);
/**
 * EZS gateway monitor v1 — read-only and non-destructive.
 * Usage: php bin/gateway_monitor.php once|watch [seconds]
 * Never starts, kills, binds or reconfigures processes.
 */
$root=dirname(__DIR__);
$action=$argv[1]??'once';
if(!in_array($action,['once','watch'],true)){fwrite(STDERR,"EZS_GATEWAY_MONITOR_BAD_ACTION\n");exit(2);}
$interval=filter_var($argv[2]??'5',FILTER_VALIDATE_INT);
if($action==='watch'&&($interval===false||$interval<2||$interval>3600)){fwrite(STDERR,"EZS_GATEWAY_MONITOR_BAD_INTERVAL\n");exit(2);}
require_once $root.'/src/Module/Infrastructure/WindowsPortOwnership.php';
use Ezs\Web\Module\Infrastructure\WindowsPortOwnership;
function probeGateway(int $port): array {
 $ctx=stream_context_create(['http'=>['timeout'=>2,'ignore_errors'=>true,'follow_location'=>0]]);
 $raw=@file_get_contents("http://127.0.0.1:$port/__ezscore_gateway_status",false,$ctx);
 $headers=$http_response_header??[];
 $http=preg_match('~^HTTP/\S+\s+(\d{3})~',(string)($headers[0]??''),$m)?(int)$m[1]:0;
 $j=is_string($raw)?json_decode($raw,true):null;
 $valid=$http===200&&is_array($j)&&($j['ok']??false)===true
     &&($j['protocol']??'')==='ezscore.online-gateway.v3'
     &&($j['backend_port']??null)===8511;
 return ['http'=>$http,'protocol_valid'=>$valid,'maintenance'=>$valid?($j['maintenance']??null):null];
}
function snapshotGateway(string $root): array {
 $path=$root.'/runtime/v2-prod/processes.json';
 $state=is_file($path)?json_decode((string)file_get_contents($path),true):null;
 $pid=is_array($state)?(int)($state['gateway_pid']??0):0;
 $status=probeGateway(8510);
 $identity=$pid>0?WindowsPortOwnership::snapshot(['prod_gateway'=>[8510,$pid,'python.exe']]):['available'=>false,'reason'=>'prod_state_missing'];
 $identityOk=($identity['checks']['prod_gateway']['verified']??false)===true;
 $healthy=$identityOk&&$status['protocol_valid'];
 return [
  'schema'=>'ezs.gateway.monitor.v1','timestamp_utc'=>gmdate('c'),'mode'=>'READ_ONLY',
  'prod_gateway'=>['port'=>8510,'pid_recorded'=>$pid,'http'=>$status['http'],
    'protocol_valid'=>$status['protocol_valid'],'maintenance'=>$status['maintenance'],
    'port_pid_image_verified'=>$identityOk,'healthy'=>$healthy],
  'limitations'=>['No full executable path, command-line or process start-time attestation',
    'No lifecycle actions; Python PROD remains authoritative',
    'SSO and real media streaming are not verified'],
  'safe_to_cutover'=>false
 ];
}
do{
 $result=snapshotGateway($root);
 echo json_encode($result,JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
 if($action==='once')exit($result['prod_gateway']['healthy']?0:1);
 if(!$result['prod_gateway']['healthy'])fwrite(STDERR,"EZS_GATEWAY_MONITOR_ALERT\n");
 sleep($interval);
}while(true);
