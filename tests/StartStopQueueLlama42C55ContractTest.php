<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
$queue=(string)file_get_contents($root.'/src/Module/Coordination/LabQueueProbe.php');
$caddy=(string)file_get_contents($root.'/config/caddy/Caddyfile.dev-lab-assistant-candidate');
foreach(['Invoke-EzsRootLifecycle -Action start','Invoke-EzsLabAssistantLifecycle -Action start','Invoke-EzsProdLifecycle -Action start','Invoke-EzsAssistantAiLifecycle -Action start','Caddyfile.prod-unified','PersistedProdMode','EZS_PROD_START_NORMAL_RESTORED'] as $v){
 if(!str_contains($start,$v))throw new RuntimeException('START_MISSING:'.$v);
}
foreach(['Invoke-EzsRootLifecycle -Action stop','Invoke-EzsLabAssistantLifecycle -Action stop','Invoke-EzsAssistantAiLifecycle -Action stop'] as $v){
 if(!str_contains($stop,$v))throw new RuntimeException('STOP_MISSING:'.$v);
}
if(str_contains($stop,'prod_mode.php')||str_contains($stop,'function Invoke-EzsProdLifecycle')||str_contains($stop,'EZS_PROD_STOP_OWNED_OK'))throw new RuntimeException('STOP_TOUCHES_PROD');
if(substr_count($start,'function Invoke-EzsAssistantAiLifecycle')!==1)throw new RuntimeException('LLAMA_LIFECYCLE_MISSING_OR_DUPLICATED');
if(!str_contains($start,'8720')||!str_contains($stop,'8720'))throw new RuntimeException('LLAMA_PORT_MISSING');
if(!str_contains($queue,'http://127.0.0.1:8702/internal/analysis/desktop/jobs/queue'))throw new RuntimeException('QUEUE_LAB_ENDPOINT_CHANGED');
if(!str_contains($caddy,'php_fastcgi 127.0.0.1:8701')||!str_contains($caddy,'http://127.0.0.1:8702'))throw new RuntimeException('QUEUE_LAB_FACADE_CHANGED');
echo "EZS_START_STOP_QUEUE_LLAMA_COMPAT_OK\n";
