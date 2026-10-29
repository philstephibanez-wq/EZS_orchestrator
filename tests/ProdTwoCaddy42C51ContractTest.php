<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$caddy=(string)file_get_contents($root.'/config/caddy/Caddyfile.prod-unified');
foreach([':8501 {',':8510 {',':8511 {','127.0.0.1:8512','127.0.0.1:18515','forward_auth 127.0.0.1:8510','/internal/media/auth'] as $required){
 if(!str_contains($caddy,$required))throw new RuntimeException('CADDY_MISSING '.$required);
}
if(substr_count($caddy,'admin 127.0.0.1:2020')!==1)throw new RuntimeException('PROD_ADMIN');
foreach(['start.ps1','stop.ps1'] as $script){
 $src=(string)file_get_contents($root.'/scripts/'.$script);
 $i=strpos($src,'function Invoke-EzsProdLifecycle {');
 $j=strpos($src,'EZS_PROD_STOP_OWNED_OK',$i===false?0:$i);
 if($i===false||$j===false)throw new RuntimeException('LIFECYCLE_MISSING');
 $prod=substr($src,$i,$j-$i);
 foreach(['ezs.prod.php.v1','ezs.prod.php.v2','ezs.prod.php.v2','Caddyfile.prod-unified','EZS_PROD_START_MAINTENANCE_OK','EZS_PROD_STOP_OWNED_OK'] as $required){
  if(!str_contains($src,$required))throw new RuntimeException('LIFECYCLE_MISSING '.$required.' '.$script);
 }
 $seqStart=strpos($prod,'$sequence=@(');
 $seqEnd=$seqStart===false?false:strpos($prod,'$record=[ordered]', $seqStart);
 if($seqStart===false||$seqEnd===false)throw new RuntimeException('SEQUENCE_MISSING');
 $seq=substr($prod,$seqStart,$seqEnd-$seqStart);
 if(substr_count($seq,'bin=$caddy')!==1||substr_count($seq,'bin=$php')!==2)throw new RuntimeException('NOT_ONE_PROD_CADDY '.$script);
 if(str_contains($seq,"name='internal_pid'")||str_contains($seq,"name='gateway_pid'"))throw new RuntimeException('LEGACY_LAUNCH '.$script);
 if(!str_contains($prod,'[array]::Reverse($started)'))throw new RuntimeException('ROLLBACK_MISSING');
}
echo "EZS_PROD_TWO_CADDY_4_2C51_OK\n";
