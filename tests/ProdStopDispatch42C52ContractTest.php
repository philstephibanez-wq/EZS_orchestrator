<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
if(!str_starts_with($stop,'param()'))throw new RuntimeException('STOP_MUST_BE_DEV_ONLY');
if(str_contains($stop,"if(".'$ProdAction'." -ne '')"))throw new RuntimeException('STOP_HAS_PROD_DISPATCH');
if(str_contains($stop,"& ".'$php'." ".'$entry'." maintenance"))throw new RuntimeException('STOP_CHANGES_PROD_MAINTENANCE');
if(strpos($start,"Invoke-EzsProdLifecycle -Action start")===false)throw new RuntimeException('STANDARD_START_MUST_RECONCILE_PROD');
if(strpos($start,"Invoke-EzsLabAssistantLifecycle -Action start")===false)throw new RuntimeException('STANDARD_START_MUST_START_LAB');
if(strpos($start,"Invoke-EzsRootLifecycle -Action start")===false)throw new RuntimeException('STANDARD_START_MUST_START_DEV');
if(strpos($start,"Invoke-EzsAssistantAiLifecycle -Action start")===false)throw new RuntimeException('STANDARD_START_MUST_START_ASSISTANT_AI');
echo "EZS_LIFECYCLE_DEV_STOP_PROD_START_OK\n";
