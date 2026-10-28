<?php
declare(strict_types=1);
/**
 * EZScore PROD gateway candidate (PHP). Run exclusively on a test port until accepted.
 * php -S 127.0.0.1:8513 -t runtime_components/prod_gateway_php runtime_components/prod_gateway_php/router.php
 * This router relies on PHP's built-in server; it is not a production process manager.
 */
$config='H:/EZScore/var/runtime/online-gateway.json';
// Recipe-only diagnostic: no secrets or configuration path disclosed.
$testConfig=getenv('EZS_GATEWAY_RECIPE_CONFIG');
if(is_string($testConfig)&&$testConfig!==''){
 $port=(int)($_SERVER['SERVER_PORT']??0);
 $script=(string)($_SERVER['SCRIPT_FILENAME']??'');
 $expected=realpath(__FILE__);
 $scriptReal=realpath($script);
 $exists=is_file($testConfig);
 $mode=getenv('EZS_GATEWAY_RECIPE_MODE');
 $portAllowed=$port===18513 || $mode==='isolated-fastcgi-v1';
 $realConfig=realpath($testConfig);
 $tempRoot=realpath(sys_get_temp_dir());
 $configIsTemp=$realConfig!==false&&$tempRoot!==false&&
     str_starts_with(strtolower(str_replace('\\','/',$realConfig)),
                     strtolower(rtrim(str_replace('\\','/',$tempRoot),'/').'/ezs-gateway-'));
 $scriptAllowed=$scriptReal!==false&&$expected!==false&&
     strcasecmp(str_replace('\\','/',$scriptReal),str_replace('\\','/',$expected))===0;
 if(!$portAllowed||!$exists||!$scriptAllowed||!$configIsTemp){
  http_response_code(503);
  header('Content-Type: application/json; charset=utf-8');
  header('Cache-Control: no-store');
  echo json_encode(['error'=>'gateway_recipe_refused','server_port'=>$port,
    'config_exists'=>$exists,'script_matches'=>$scriptAllowed,'config_is_temp'=>$configIsTemp,
    'script_filename_present'=>$script!==''],JSON_THROW_ON_ERROR);
  return;
 }
 $config=$testConfig;
}
$uri=$_SERVER['HTTP_X_EZS_ORIGINAL_URI']??($_SERVER['REQUEST_URI']??'/');
// Only the trusted loopback Caddy candidate is permitted to set this header in the recipe.
if(!is_string($uri)||!str_starts_with($uri,'/')||str_starts_with($uri,'//')){http_response_code(400);return;}
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
 $body='<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="20"><title>EZScore — Maintenance</title>
<style>body{margin:0;background:#101820;color:#eef5f7;font:16px Segoe UI,Arial,sans-serif}.wrap{max-width:760px;margin:12vh auto;padding:32px}.card{background:#18242d;border:1px solid #30434f;border-radius:16px;padding:28px;box-shadow:0 20px 60px #0005}h1{margin:0 0 10px;font-size:34px}p{color:#b9c8d1;line-height:1.6}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#f0ad4e;margin-right:10px}.small{font-size:13px;color:#81939e}</style>
</head><body><div class="wrap"><div class="card"><h1>EZScore</h1><p><span class="dot"></span><strong>Maintenance en cours</strong></p><p>Le service sera de nouveau disponible dans quelques instants.</p><p class="small">Cette page se recharge automatiquement.</p></div></div></body></html>';
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
 if($isInternal){header('Retry-After: 2');reply(503,'{"error":"online_backend_unavailable"}','application/json');}
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
