<?php
declare(strict_types=1);
/**
 * Single-command isolated gateway recipe. It owns only the three processes it spawns.
 * Never probes or changes PROD ports or settings.
 */
$root=dirname(__DIR__);
$base=rtrim(sys_get_temp_dir(),'\\/').'/ezs-gateway-recipe-v2a36';
$config=$base.'/var/runtime/online-gateway.json';
$ports=[18511,18510,18513];
$jobs=[];
$logs=[];
function freePort(int $port): bool {
 $errno=0;$errstr='';
 $s=@stream_socket_client('tcp://127.0.0.1:'.$port,$errno,$errstr,0.25);
 if(is_resource($s)){fclose($s);return false;}
 return true;
}
function readStatus(int $port,string $path): ?array {
 $ctx=stream_context_create(['http'=>['timeout'=>1,'ignore_errors'=>true,'follow_location'=>0]]);
 $raw=@file_get_contents('http://127.0.0.1:'.$port.$path,false,$ctx);
 if(!is_string($raw))return null;
 return json_decode($raw,true);
}
function spawnRecipe(array $command,string $root,array $env,string $log): array {
 $descriptors=[0=>['file',PHP_OS_FAMILY==='Windows'?'NUL':'/dev/null','r'],
 1=>['file',$log.'.out','a'],2=>['file',$log.'.err','a']];
 $options=PHP_OS_FAMILY==='Windows'?['bypass_shell'=>true,'create_new_console'=>false]:[];
 $process=@proc_open($command,$descriptors,$pipes,$root,$env,$options);
 if(!is_resource($process))throw new RuntimeException('EZS_RECIPE_PROCESS_START_FAILED');
 $pid=proc_get_status($process)['pid']??0;
 return [$process,(int)$pid];
}
try {
 foreach($ports as $port)if(!freePort($port))throw new RuntimeException("EZS_RECIPE_PORT_OCCUPIED_$port — no processes started");
 if(!is_dir(dirname($config))&&!mkdir(dirname($config),0770,true)&&!is_dir(dirname($config)))
  throw new RuntimeException('EZS_RECIPE_TEMP_DIR_FAILED');
 $json=json_encode(['maintenance'=>false,'backend_host'=>'127.0.0.1','backend_port'=>18511],JSON_THROW_ON_ERROR);
 if(file_put_contents($config,$json)===false)throw new RuntimeException('EZS_RECIPE_CONFIG_WRITE_FAILED');
 $env=getenv();
 $env=is_array($env)?$env:[];
 $php=PHP_BINARY;
 $python='H:/Python/pythoncore-3.14-64/python.exe';
 if(!is_file($python))throw new RuntimeException('EZS_RECIPE_PYTHON_MISSING: '.$python);
 $definitions=[
  [[$php,'-S','127.0.0.1:18511',$root.'/runtime_components/prod_gateway_php/recipe_backend.php'],18511,'backend'],
  [[$python,$root.'/runtime_components/prod_gateway/server.py','--root',$base,'--host','127.0.0.1','--port','18510'],18510,'python'],
  [[$php,'-S','127.0.0.1:18513','-t',$root.'/runtime_components/prod_gateway_php',
    $root.'/runtime_components/prod_gateway_php/router.php'],18513,'php']
 ];
 foreach($definitions as [$command,$port,$label]){
  $childEnv=$env;
  if($label==='php')$childEnv['EZS_GATEWAY_RECIPE_CONFIG']=$config;
  else unset($childEnv['EZS_GATEWAY_RECIPE_CONFIG']);
  $log=$base.'/autotest-'.$label;
  [$process,$pid]=spawnRecipe($command,$root,$childEnv,$log);
  $jobs[]=[$process,$pid,$label];
  $ready=false;
  for($i=0;$i<40;$i++){
   usleep(150000);
   if(!proc_get_status($process)['running'])break;
   $probe=$label==='backend'?readStatus($port,'/probe'):readStatus($port,'/__ezscore_gateway_status');
   if(is_array($probe)&&($label==='backend'?($probe['path']??null)==='/probe':
       ($probe['backend_port']??null)===18511)){$ready=true;break;}
  }
  if(!$ready)throw new RuntimeException("EZS_RECIPE_START_TIMEOUT_$label (logs: $log.err)");
 }
 // Existing comparer performs the 10 parity checks and returns a failing exit code on differences.
 $command=[$php,$root.'/bin/gateway_recipe.php','compare'];
 $proc=@proc_open($command,[0=>['file',PHP_OS_FAMILY==='Windows'?'NUL':'/dev/null','r'],
  1=>['pipe','w'],2=>['pipe','w']],$pipes,$root,$env,
  PHP_OS_FAMILY==='Windows'?['bypass_shell'=>true,'create_new_console'=>false]:[]);
 if(!is_resource($proc))throw new RuntimeException('EZS_RECIPE_COMPARE_START_FAILED');
 $out=stream_get_contents($pipes[1]);fclose($pipes[1]);
 $err=stream_get_contents($pipes[2]);fclose($pipes[2]);
 $code=proc_close($proc);
 echo $out;
 if($err!=='')fwrite(STDERR,$err);
 if($code!==0 || !str_contains($out,'EZS_PHP_GATEWAY_RECIPE_PARITY_OK'))throw new RuntimeException('EZS_RECIPE_COMPARE_FAILED');
 echo "EZS_GATEWAY_AUTOTEST_OK\n";
} catch(Throwable $e) {
 fwrite(STDERR,$e->getMessage()."\n");
 $failed=true;
} finally {
 foreach(array_reverse($jobs) as [$process,$pid,$label]){
  $status=proc_get_status($process);
  if($status['running'])proc_terminate($process);
  // Only process resources returned by this invocation may be terminated.
  proc_close($process);
 }
 echo 'EZS_RECIPE_CREATED_PROCESSES_CLEANED_UP'."\n";
}
exit(($failed??false)?1:0);
