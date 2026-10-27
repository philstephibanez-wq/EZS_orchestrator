<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$template=file_get_contents($root.'/templates/infrastructure/index.html.twig');
$controller=file_get_contents($root.'/src/Module/Infrastructure/Controller/HomeController.php');
foreach(['DEV · EZScore','PROD · EZScore','LAB · EZStudio','Assistant','Indéterminée','orchestrator_version','ezs-server-grid'] as $marker) {
  if (!str_contains($template,$marker)) throw new RuntimeException('missing_'.$marker);
}
if (!str_contains($controller,"'VERSION'")) throw new RuntimeException('version_not_loaded');
if (str_contains($template,'EZS Orchestrator V2')) throw new RuntimeException('legacy_title');
echo "SERVER_CARDS_OK\n";
