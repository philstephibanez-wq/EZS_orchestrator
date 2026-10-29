<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2c33')throw new RuntimeException('VERSION');
$start=(string)file_get_contents($r.'/scripts/start.ps1');
$twig=(string)file_get_contents($r.'/templates/jobs/index.html.twig');
$ctrl=(string)file_get_contents($r.'/src/Module/Coordination/Controller/JobsPageController.php');
if(str_contains($twig,'lab_queue')||str_contains($twig,'sonde LAB')||str_contains($twig,'observation partielle'))throw new RuntimeException('OLD_QUEUE_PANEL');
if(str_contains($ctrl,'LabQueueProbe'))throw new RuntimeException('OLD_QUEUE_PROBE');
foreach(['EZS_START_STALE_STATE_AFTER_REBOOT_CLEARED','EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED','Remove-Item -LiteralPath $stateFile','8790, 8791, 8502, 8852, 8702, 8712','ProcessInfo $savedCaddyId','ProcessInfo $savedPhpId'] as $term){
 if(!str_contains($start,$term))throw new RuntimeException('START_GUARD_MISSING: '.$term);
}
if(strpos($start,'EZS_START_STALE_STATE_AFTER_REBOOT_CLEARED')>strpos($start,'$phpId = [int]$s.php_pid'))throw new RuntimeException('RECOVERY_AFTER_BRANCH');
echo "EZS_POST_REBOOT_START_AND_QUEUE_4_2C33_OK\n";
