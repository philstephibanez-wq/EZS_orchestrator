<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c16')throw new RuntimeException('VERSION');
foreach(['start','stop'] as $a){
    $s=(string)file_get_contents($root.'/scripts/'.$a.'.ps1');
    foreach(['function Invoke-EzsAssistantAiLifecycle','ezs.assistant.ai.v1','assistant-ai.lock','assistant-ai.json','CreationDate','ExecutablePath','OwningProcess','--gpu-layers','--ctx-size','8720',"Invoke-EzsAssistantAiLifecycle -Action $a"] as $needle){
        if(!str_contains($s,$needle))throw new RuntimeException($a.':'.$needle);
    }
}
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
if(!str_contains($start,'EZS_AI_EXISTING_UNMANAGED_LISTENER_PRESERVED')||!str_contains($stop,'EZS_AI_STOP_UNMANAGED_PRESERVED'))throw new RuntimeException('UNMANAGED_PROTECTION');
echo "EZS_ASSISTANT_AI_LIFECYCLE_4_2C16_OK\n";
