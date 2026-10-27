<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$twig=(string)file_get_contents($root.'/templates/infrastructure/legacy_home.html.twig');
foreach (['class="sidebar"','/api/status','/api/jobs','/api/logs','/api/action','/api/deployment/','/api/assistant/','{{ orchestrator_version'] as $term) {
 if (!str_contains($twig,$term)) throw new RuntimeException('HISTORIC_HOME_PARITY_MISSING:'.$term);
}
if (str_contains($twig,'__TOKEN__'))throw new RuntimeException('UNREPLACED_HISTORY_TOKEN');
echo "SYMFONY_HISTORIC_HOME_VIEW_PARITY_OK\n";
