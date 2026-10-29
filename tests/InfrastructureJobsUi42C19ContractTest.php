<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim(file_get_contents($r.'/VERSION'))!=='4.2c19')throw new RuntimeException('VERSION');
$i=file_get_contents($r.'/templates/infrastructure/index.html.twig');
$j=file_get_contents($r.'/templates/jobs/index.html.twig');
$h=file_get_contents($r.'/src/Module/Infrastructure/Controller/HomeController.php');
$c=file_get_contents($r.'/src/Module/Coordination/Controller/JobsPageController.php');
if(substr_count($i,'class="small mt-2 mb-0 ezs-tech-grid"')!==4)throw new RuntimeException('FOUR_CARDS');
foreach(['Façade','Backend','Autorité Orchestrator','Action','État complémentaire'] as $label){if(substr_count($i,'<dt>'.$label.'</dt>')!==4)throw new RuntimeException('DETAIL_LABEL');}
if(!str_contains($i,'lab_queue_status.connected')||!str_contains($i,'assistant_readiness.inference'))throw new RuntimeException('INFRA_SONDES');
if(str_contains($j,'Assistant — disponibilité IA')||str_contains($j,'assistant_readiness'))throw new RuntimeException('STATUS_LEAK');
if(!str_contains($j,'lab_queue.jobs')||!str_contains($j,'history'))throw new RuntimeException('BUSINESS_LOST');
if(!str_contains($h,'LabQueueProbe $labQueue')||!str_contains($h,'AssistantReadinessProbe $assistant'))throw new RuntimeException('PROBES_MISSING');
if(str_contains($c,'AssistantReadinessProbe'))throw new RuntimeException('JOB_AI_DEPENDENCY');
echo "EZS_INFRA_JOBS_UI_4_2C19_OK\n";
