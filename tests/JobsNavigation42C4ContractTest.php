<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2c4')throw new RuntimeException('VERSION');
$home=(string)file_get_contents($r.'/templates/infrastructure/index.html.twig');
$page=(string)file_get_contents($r.'/templates/jobs/index.html.twig');
$controller=(string)file_get_contents($r.'/src/Module/Coordination/Controller/JobsPageController.php');
$legacy=(string)file_get_contents($r.'/src/Module/Infrastructure/Controller/LegacyReadOnlyController.php');
foreach([['home jobs link',str_contains($home,'href="/jobs"')],['route',str_contains($controller,"#[Route('/jobs'")],['read-only page',str_contains($page,'aucune exécution')],['no invented jobs',str_contains($page,'aucun job n\'est présenté')],['api remains 503',str_contains($legacy,"jobs_migration_pending")]] as [$name,$valid])if(!$valid)throw new RuntimeException($name);
echo "EZS_JOBS_NAVIGATION_4_2C4_OK\n";
