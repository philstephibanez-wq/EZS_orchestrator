<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
if(trim((string)file_get_contents(dirname(__DIR__).'/VERSION'))!=='4.2c17')throw new RuntimeException('VERSION');
if(substr_count($s,'function Invoke-EzsAssistantAiLifecycle')!==1)throw new RuntimeException('DUPLICATE');
if(substr_count($s,'Invoke-EzsAssistantAiLifecycle -Action start')!==2)throw new RuntimeException('CALL_COUNT');
if(strpos($s,'function Invoke-EzsAssistantAiLifecycle')>strpos($s,"Write-Host 'EZS_DEV_APPS_ALREADY_RUNNING_VERIFIED'"))throw new RuntimeException('DECLARATION_LATE');
$branch="/Invoke-EzsLabAssistantLifecycle -Action start\\s+if\\(-not \\?\\)\\{throw 'EZS_LA_START_FAILED'\\}\\s+Invoke-EzsAssistantAiLifecycle -Action start\\s+return/";
if(!preg_match($branch,$s))throw new RuntimeException('EARLY_RETURN_BYPASS');
if(str_contains($s,'[int](Listener)[0]'))throw new RuntimeException('LISTENER_EXPRESSION');
echo "EZS_ASSISTANT_AI_START_EARLY_RETURN_4_2C17_OK\n";
