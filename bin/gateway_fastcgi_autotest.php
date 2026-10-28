<?php
declare(strict_types=1);
// Local integration harness. Only its own proc_open handles may be terminated.
$root=dirname(__DIR__);
$dir=rtrim(sys_get_temp_dir(),'\\/').'/ezs-gateway-fastcgi-v2a41';
$cfg=$dir.'/online-gateway.json';
$ports=[18511,18514,18515];
$jobs=[];$failed=false;
function requestLocal(int $port,string $path): array {
 $ctx=stream_context_create(['http'=>['timeout'=>2,'ignore_errors'=>true,'follow_location'=>0,'header'=>"Host: ezscore.test\r\nX-Forwarded-Proto: https\r\n"]]);
 $body=@file_get_contents('http://127.0.0.1:'.$port.$path,false,$ctx);
 $hs=$http_response_header??[];
 $code=preg_match('~^HTTP/\S+ (\d{3})~',$hs[0]??'',$m)?(int)$m[1]:0;
 return ['code'=>$code,'body'=>is_string($body)?$body:''];
}
function freeLocal(int $port): bool {
 $s=@stream_socket_client("tcp://127.0.0.1:$port",$errno,$errstr,0.2);
 if(is_resource($s)){fclose($s);return false;}return true;
}
try {
 foreach($ports as $port)if(!freeLocal($port))throw new RuntimeException("EZS_RECIPE_PORT_OCCUPIED_$port");
 if(!is_dir($dir)&&!mkdir($dir,0770,true)&&!is_dir($dir))throw new RuntimeException('TEMP_DIRECTORY_FAILED');
 $payload=['maintenance'=>false,'backend_host'=>'127.0.0.1','backend_port'=>18511];
 file_put_contents($cfg,json_encode($payload,JSON_THROW_ON_ERROR));
 $env=getenv();$env=is_array($env)?$env:[];
 $env['EZS_GATEWAY_RECIPE_CONFIG']=$cfg;
 $cmds=[
  ['mock',18511,[PHP_BINARY,'-S','127.0.0.1:18511',$root.'/runtime_components/prod_gateway_php/recipe_backend.php']],
  ['fastcgi',18515,['H:/PHP/php-8.5-x64/php-cgi.exe','-b','127.0.0.1:18515']],
  ['caddy',18514,['H:/Caddy/caddy.exe','run','--config',$root.'/config/caddy/Caddyfile.gateway-php-candidate','--adapter','caddyfile']]
 ];
 foreach($cmds as [$label,$port,$command]){
  if(!is_file($command[0]))throw new RuntimeException("BINARY_NOT_FOUND_$label");
  $childEnv=$env;
  if($label==='fastcgi'){$childEnv['EZS_GATEWAY_RECIPE_MODE']='isolated-fastcgi-v1';$childEnv['PHP_FCGI_MAX_REQUESTS']='0';$childEnv['APP_ENV']='prod';$childEnv['APP_DEBUG']='0';}
  $desc=[0=>['file',PHP_OS_FAMILY==='Windows'?'NUL':'/dev/null','r'],1=>['file',$dir.'/'.$label.'.out','a'],2=>['file',$dir.'/'.$label.'.err','a']];
  $proc=@proc_open($command,$desc,$pipes,$root,$childEnv,PHP_OS_FAMILY==='Windows'?['bypass_shell'=>true,'create_new_console'=>false]:[]);
  if(!is_resource($proc))throw new RuntimeException("START_FAILED_$label");
  $jobs[]=['process'=>$proc,'label'=>$label];
  $ready=false;
  for($i=0;$i<50;$i++){
   usleep(150000);
   if(!proc_get_status($proc)['running'])break;
   if(!freeLocal($port)){$ready=true;break;}
  }
  if(!$ready)throw new RuntimeException("START_TIMEOUT_$label (see $dir/$label.err)");
 }
 foreach(['/probe?test=alpha%20beta','/internal/media/auth?token=42'] as $path){
  $r=requestLocal(18514,$path);
  $data=json_decode($r['body'],true);
  if($r['code']!==200||!is_array($data)||($data['uri']??null)!==$path||($data['forwarded_proto']??null)!=='https'){
   fwrite(STDERR,json_encode(['path'=>$path,'response'=>$r],JSON_UNESCAPED_SLASHES)."\n");
   throw new RuntimeException('FASTCGI_URI_OR_HEADERS_MISMATCH');
  }
  echo "MATCH FASTCGI GET $path HTTP 200\n";
 }
 file_put_contents($cfg,json_encode(['maintenance'=>true,'backend_host'=>'127.0.0.1','backend_port'=>18511],JSON_THROW_ON_ERROR));
 $m=requestLocal(18514,'/probe');
 if($m['code']!==503)throw new RuntimeException('FASTCGI_MAINTENANCE_MISMATCH');
 echo "MATCH FASTCGI MAINTENANCE HTTP 503\n";
 echo "EZS_GATEWAY_FASTCGI_AUTOTEST_OK\n";
}catch(Throwable $e){
 $failed=true;fwrite(STDERR,$e->getMessage()."\n");
}finally{
 foreach(array_reverse($jobs) as $job){
  $p=$job['process'];$status=proc_get_status($p);
  if($status['running'])proc_terminate($p);
  proc_close($p);
 }
 echo "EZS_GATEWAY_FASTCGI_AUTOTEST_CLEANED_UP\n";
}
exit($failed?1:0);
