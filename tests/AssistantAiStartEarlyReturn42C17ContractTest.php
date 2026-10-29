<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
if(trim((string)file_get_contents(dirname(__DIR__).'/VERSION'))!=='4.2c18')throw new RuntimeException('VERSION');
if(substr_count($s,'function Invoke-EzsAssistantAiLifecycle')!==1)throw new RuntimeException('DUPLICATE');
if(substr_count($s,'Invoke-EzsAssistantAiLifecycle -Action start')!==2)throw new RuntimeException('CALL_COUNT');
if(strpos($s,'function Invoke-EzsAssistantAiLifecycle')>strpos($s,"Write-Host 'EZS_DEV_APPS_ALREADY_RUNNING_VERIFIED'"))throw new RuntimeException('DECLARATION_LATE');
$branchStart=strpos($s,"Write-Host 'EZS_DEV_APPS_ALREADY_RUNNING_VERIFIED'");
$branchEnd=strpos($s,"\n        }",$branchStart);
if($branchStart===false || $branchEnd===false)throw new RuntimeException('BRANCH_MISSING');
$branch=substr($s,$branchStart,$branchEnd-$branchStart);
$required=[
    'Invoke-EzsLabAssistantLifecycle -Action start',
    "if(-not $?){throw 'EZS_LA_START_FAILED'}",
    'Invoke-EzsAssistantAiLifecycle -Action start',
    'return'
];
$last=-1;
foreach($required as $fragment){
    $at=strpos($branch,$fragment);
    if($at===false || $at<=$last)throw new RuntimeException('EARLY_RETURN_BYPASS');
    $last=$at;
}
if(str_contains($s,'[int](Listener)[0]'))throw new RuntimeException('LISTENER_EXPRESSION');
echo "EZS_ASSISTANT_AI_START_EARLY_RETURN_4_2C17_OK\n";
