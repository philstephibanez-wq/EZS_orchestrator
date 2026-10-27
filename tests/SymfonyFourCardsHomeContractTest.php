<?php
declare(strict_types=1);

$root = dirname(__DIR__);
if (is_file($root . '/templates/infrastructure/legacy_home.html.twig')) {
    throw new RuntimeException('INACTIVE_LEGACY_HOME_STILL_PRESENT');
}
$home = (string) file_get_contents($root . '/src/Module/Infrastructure/Controller/HomeController.php');
if (!str_contains($home, "'infrastructure/index.html.twig'")) {
    throw new RuntimeException('FOUR_CARDS_HOME_NOT_ROUTED');
}
$view = (string) file_get_contents($root . '/templates/infrastructure/index.html.twig');
foreach (['DEV · EZScore', 'PROD · EZScore', 'LAB · EZStudio', 'Assistant', "_gpu_monitor.html.twig"] as $marker) {
    if (!str_contains($view, $marker)) {
        throw new RuntimeException('HOME_CARD_OR_PROBE_MISSING');
    }
}
echo "SYMFONY_FOUR_CARDS_HOME_CONTRACT_OK\n";
