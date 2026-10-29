<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
$a=strpos($s,'function Invoke-EzsAssistantAiLifecycle');
$b=strpos($s,'function Invoke-EzsRootLifecycle',$a);
$p=substr($s,$a,$b-$a);
foreach(['function Ai-Identity','function Ai-TcpReachable','EZS_AI_STALE_STATE_AFTER_REBOOT_CLEARED','Ai-Identity $record','Ai-TcpReachable','EZS_AI_START_REFUSED_UNHEALTHY_EXISTING_PROCESS','if(-not(Owned $s)){throw'] as $needle){if(!str_contains($p,$needle))throw new RuntimeException('MISSING: '.$needle);}
echo "EZS_AI_REBOOT_4_2C45_OK\n";
