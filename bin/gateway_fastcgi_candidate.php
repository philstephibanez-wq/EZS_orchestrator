<?php
declare(strict_types=1);
// Static deployment preparation only; does not start or stop any process.
$root=dirname(__DIR__);
$config=$root.'/config/caddy/Caddyfile.gateway-php-candidate';
$router=$root.'/runtime_components/prod_gateway_php/router.php';
$requirements=[
 'PHP FastCGI candidate must listen on loopback 18515 and be supervised.',
 'Caddy candidate must bind only loopback 18514, never the public 8501.',
 'FastCGI routing must preserve original REQUEST_URI including query string.',
 'Run functional SSO and media verification before changing 8510.',
 'Keep Python launcher and rollback until a real cutover is approved.',
];
$files=is_file($config)&&is_file($router);
$syntax=null;
$caddy='H:/Caddy/caddy.exe';
if($files&&is_file($caddy)){
 $cmd=[$caddy,'validate','--config',$config,'--adapter','caddyfile'];
 $p=@proc_open($cmd,[0=>['file',PHP_OS_FAMILY==='Windows'?'NUL':'/dev/null','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,$root,null,PHP_OS_FAMILY==='Windows'?['bypass_shell'=>true]:[]);
 if(is_resource($p)){
  $out=stream_get_contents($pipes[1]);fclose($pipes[1]);
  $err=stream_get_contents($pipes[2]);fclose($pipes[2]);
  $syntax=['valid'=>proc_close($p)===0,'error'=>trim($err)];
 }
}
echo json_encode(['schema'=>'ezs.gateway.fastcgi.candidate.v1','mode'=>'READ_ONLY',
 'files_present'=>$files,'caddy_validation'=>$syntax,'unverified_requirements'=>$requirements,
 'prod_cutover_authorized'=>false],JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
if(!$files||($syntax!==null&&!$syntax['valid']))exit(1);
