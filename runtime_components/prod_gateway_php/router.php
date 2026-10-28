<?php
declare(strict_types=1);
/**
 * EZScore PROD gateway candidate (PHP). Run exclusively on a test port until accepted.
 * php -S 127.0.0.1:8513 -t runtime_components/prod_gateway_php runtime_components/prod_gateway_php/router.php
 * This router relies on PHP's built-in server; it is not a production process manager.
 */
$config='H:/EZScore/var/runtime/online-gateway.json';
// Test override is forbidden on PROD 8510 and requires an existing isolated config.
$testConfig=getenv('EZS_GATEWAY_RECIPE_CONFIG');
if(is_string($testConfig)&&$testConfig!==''){
 if((int)($_SERVER['SERVER_PORT']??0)===8510||!is_file($testConfig)||
    !in_array((string)($_SERVER['SERVER_NAME']??''),['127.0.0.1','localhost','::1'],true)){
  http_response_code(503);echo 'gateway_recipe_refused';return;
 }
 $config=$testConfig;
}
$uri=$_SERVER['REQUEST_URI']??'/';
$path=(string)(parse_url($uri,PHP_URL_PATH)??'/');
$method=$_SERVER['REQUEST_METHOD']??'GET';
$head=$method==='HEAD';
$raw=@file_get_contents($config);
$settings=is_string($raw)?json_decode($raw,true):null;
$settings=is_array($settings)?$settings:[];
function reply(int $status,string $payload,string $type): void {
 global $head;
 http_response_code($status);
 header('Content-Type: '.$type);
 header('Content-Length: '.strlen($payload));
 header('Cache-Control: no-store');
 if(!$head)echo $payload;
}
if($path==='/__ezscore_gateway_health'){reply(200,'OK','text/plain; charset=utf-8');return;}
if($path==='/__ezscore_gateway_status'){
 reply(200,json_encode(['ok'=>true,'protocol'=>'ezscore.online-gateway.v3',
 'maintenance'=>(bool)($settings['maintenance']??false),'backend_host'=>(string)($settings['backend_host']??'127.0.0.1'),
 'backend_port'=>(int)($settings['backend_port']??8511)],JSON_THROW_ON_ERROR),'application/json; charset=utf-8');return;
}
$isInternal=false;
foreach(['/internal/analysis/desktop','/internal/analysis/worker','/internal/media/auth'] as $prefix){
 if(str_starts_with($path,$prefix)){$isInternal=true;break;}
}
$maintenance=(bool)($settings['maintenance']??false);
function maintenancePage(): void {
 $body='<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="20"><title>EZScore — Maintenance</title></head><body><main><h1>EZScore</h1><p>Maintenance en cours</p><p>Le service sera de nouveau disponible dans quelques instants.</p></main></body></html>';
 header('Retry-After: 20');reply(503,$body,'text/html; charset=utf-8');
}
if($maintenance&&!$isInternal){maintenancePage();return;}
$host=(string)($settings['backend_host']??'127.0.0.1');
$port=(int)($settings['backend_port']??8511);
$recipeActive=is_string($testConfig)&&$testConfig!=='';
if($host!=='127.0.0.1'||($recipeActive?$port!==18511:$port!==8511)){reply(503,'{"error":"invalid_gateway_backend"}','application/json');return;}
$headers=[];
foreach(getallheaders() as $key=>$value){
 if(in_array(strtolower($key),['host','connection','proxy-connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','content-length','x-forwarded-proto','x-forwarded-host','x-forwarded-for'],true))continue;
 $headers[]=$key.': '.$value;
}
$client=(string)($_SERVER['REMOTE_ADDR']??'');
$forwarded=(string)($_SERVER['HTTP_X_FORWARDED_FOR']??'');
$headers[]='Host: '.($_SERVER['HTTP_HOST']??'');
$headers[]='X-Forwarded-Proto: '.($_SERVER['HTTP_X_FORWARDED_PROTO']??'https');
$headers[]='X-Forwarded-Host: '.($_SERVER['HTTP_HOST']??'');
$headers[]='X-Forwarded-For: '.($forwarded!==''?$forwarded.', '.$client:$client);
$body=file_get_contents('php://input');
$headers[]='Content-Length: '.strlen($body);
$context=stream_context_create(['http'=>['method'=>$method,'header'=>implode("\r\n",$headers),'content'=>$body,
 'timeout'=>60,'ignore_errors'=>true,'follow_location'=>0,'protocol_version'=>1.1]]);
$stream=@fopen('http://127.0.0.1:'.$port.$uri,'rb',false,$context);
if($stream===false){
 if($isInternal)reply(503,'{"error":"online_backend_unavailable"}','application/json');
 else maintenancePage();
 return;
}
$meta=stream_get_meta_data($stream);
$upstreamHeaders=$meta['wrapper_data']??[];
$status=502;
foreach($upstreamHeaders as $line){if(preg_match('~^HTTP/\\S+ (\\d{3})~',$line,$m))$status=(int)$m[1];}
http_response_code($status);
foreach($upstreamHeaders as $line){
 if(!str_contains($line,':'))continue;
 [$key,$value]=explode(':',$line,2);
 if(in_array(strtolower(trim($key)),['connection','proxy-connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','content-length'],true))continue;
 header(trim($key).':'.trim($value),false);
}
header('Connection: close');
if(!$head)fpassthru($stream);
fclose($stream);
