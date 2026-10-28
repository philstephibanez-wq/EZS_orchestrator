<?php
declare(strict_types=1);
$base=sys_get_temp_dir().'/ezs-gateway-recipe-v2a36';
$config=$base.'/var/runtime/online-gateway.json';
$action=$argv[1]??'help';
if($action==='init'){
 if(!is_dir(dirname($config)))mkdir(dirname($config),0770,true);
 $data=['maintenance'=>false,'backend_host'=>'127.0.0.1','backend_port'=>18511];
 file_put_contents($config,json_encode($data,JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR));
 echo "RECIPE_ROOT=$base\nRECIPE_CONFIG=$config\nEZS_GATEWAY_RECIPE_INIT_OK\n";exit;
}
if($action!=='compare'){fwrite(STDERR,"Usage: php bin/gateway_recipe.php init|compare\n");exit(2);}
if(!is_file($config)){fwrite(STDERR,"Run init first\n");exit(2);}
function requestRecipe(int $port,string $path,string $method='GET',string $body=''):array{
 $headers=['Host: ezscore.test','X-Forwarded-Proto: https','Cookie: session=recipe'];
 $context=stream_context_create(['http'=>['method'=>$method,'header'=>implode("\r\n",$headers),
  'content'=>$body,'ignore_errors'=>true,'follow_location'=>0,'timeout'=>8]]);
 $result=@file_get_contents('http://127.0.0.1:'.$port.$path,false,$context);
 $hs=$http_response_header??[];
 $code=preg_match('~^HTTP/\\S+ (\\d{3})~',$hs[0]??'',$m)?(int)$m[1]:0;
 $selected=[];
 foreach($hs as $line)if(str_contains($line,':')){
  [$k,$v]=explode(':',$line,2);
  if(in_array(strtolower(trim($k)),['location','set-cookie','content-type','retry-after'],true))
    $selected[strtolower(trim($k))]=trim($v);
 }
 return ['code'=>$code,'headers'=>$selected,'body'=>is_string($result)?$result:''];
}
$errors=[];
foreach([18510,18513] as $port){
 $status=requestRecipe($port,'/__ezscore_gateway_status');
 $data=json_decode($status['body'],true);
 if($status['code']!==200||!is_array($data)||($data['backend_port']??null)!==18511){
  $errors[]="port $port is not recipe-isolated (refusing comparison)";
 }
}
if($errors){foreach($errors as $error)fwrite(STDERR,$error."\n");exit(1);}
foreach([false,true] as $maintenance){
 $data=['maintenance'=>$maintenance,'backend_host'=>'127.0.0.1','backend_port'=>18511];
 file_put_contents($config,json_encode($data,JSON_THROW_ON_ERROR));
 foreach([['/probe','GET',''],['/redirect','GET',''],['/cookie','GET',''],
  ['/internal/media/auth','GET',''],['/post','POST','test-payload']] as [$path,$method,$body]){
  $reference=requestRecipe(18510,$path,$method,$body);
  $candidate=requestRecipe(18513,$path,$method,$body);
  $same=$maintenance ? ($reference['code']===$candidate['code'] && ($reference['headers']['retry-after']??null)===($candidate['headers']['retry-after']??null)) : ($reference===$candidate);
  if(!$same){
   $errors[]="DIFF mode=".($maintenance?'maintenance':'normal')." $method $path";
   echo json_encode(['reference'=>$reference,'candidate'=>$candidate],JSON_UNESCAPED_SLASHES)."\n";
  }else echo "MATCH mode=".($maintenance?'maintenance':'normal')." $method $path HTTP ".$reference['code']."\n";
 }
}
if($errors){foreach($errors as $e)fwrite(STDERR,$e."\n");exit(1);}
echo "EZS_PHP_GATEWAY_RECIPE_PARITY_OK\n";
