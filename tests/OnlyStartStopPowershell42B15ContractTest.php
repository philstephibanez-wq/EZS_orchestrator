<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2b')throw new RuntimeException('VERSION');
$ps=[];$it=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($r,FilesystemIterator::SKIP_DOTS));
foreach($it as $f){if(strtolower($f->getExtension())==='ps1' && !str_contains(str_replace('\\','/',$f->getPathname()),'/vendor/'))$ps[]=str_replace('\\','/',substr($f->getPathname(),strlen($r)+1));}
sort($ps);
if($ps!==['scripts/start.ps1','scripts/stop.ps1'])throw new RuntimeException('PS1_UNEXPECTED:'.implode(',',$ps));
foreach($ps as $p){$c=(string)file_get_contents($r.'/'.$p);foreach(['Invoke-EzsRootLifecycle','Invoke-EzsLabAssistantLifecycle','Invoke-EzsProdLifecycle'] as $needle){if(!str_contains($c,$needle))throw new RuntimeException('HELPER_MISSING:'.$needle);}}
echo "EZS_POWERSHELL_ONLY_START_STOP_4_2B15_OK\\n";
