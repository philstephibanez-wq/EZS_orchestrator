<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/stop.ps1');
$dispatch="if(". '$ProdAction' ." -ne ''){Invoke-EzsProdLifecycle -Action ". '$ProdAction' .";return}";
$pos=strpos($s,$dispatch);
$helper=strpos($s,'function Invoke-EzsLabAssistantLifecycle {');
$prod=strpos($s,'function Invoke-EzsProdLifecycle {');
$main=strpos($s,"\n".'$ErrorActionPreference'."='Stop'\n".'$root'."=(Resolve-Path",$prod);
$general=strpos($s,'EZS_STOP_MAINTENANCE_DEPENDENCY_MISSING',$main);
if($pos===false||$helper===false||$prod===false||$main===false||$general===false||!($helper<$prod&&$prod<$pos&&$pos<$main&&$main<$general)){throw new RuntimeException('PROD_STOP_DISPATCH_REGRESSION');}
if(substr_count($s,$dispatch)!==1){throw new RuntimeException('DISPATCH_DUPLICATED');}
echo "EZS_PROD_STOP_DISPATCH_4_2C52_OK\n";
