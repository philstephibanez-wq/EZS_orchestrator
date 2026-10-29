<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim(file_get_contents($r.'/VERSION'))!=='4.2c20')throw new RuntimeException('VERSION');
$i=file_get_contents($r.'/templates/infrastructure/index.html.twig');
$j=file_get_contents($r.'/templates/jobs/index.html.twig');
$h=file_get_contents($r.'/src/Module/Infrastructure/Controller/HomeController.php');
$contract=file_get_contents($r.'/docs/contracts/ORCHESTRATOR_GLOBAL_QUEUE_4_2C20.md');
if(str_contains($i,'lab_queue_status')||str_contains($h,'LabQueueProbe'))throw new RuntimeException('QUEUE_IN_INFRA');
foreach(['Queue globale','Provenance','observation partielle'] as $term){if(!str_contains($j,$term))throw new RuntimeException('MISSING_'.$term);}
if(!str_contains($contract,'Une seule queue globale'))throw new RuntimeException('WRONG_ARCHITECTURE');
echo "EZS_GLOBAL_QUEUE_UI_4_2C20_OK\n";
