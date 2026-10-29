<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/vendor/autoload.php';
require_once dirname(__DIR__) . '/src/Module/Infrastructure/InfrastructureCommand.php';
$source = (string) file_get_contents(dirname(__DIR__) . '/src/Module/Infrastructure/InfrastructureCommand.php');
foreach (['ezs:infrastructure', 'fastcgi-incident', 'observe-fastcgi', 'FastcgiIncidentReport::collect', 'FastcgiTransitionJournal::observe', 'WindowsPortOwnership::snapshot', 'Symfony\\Component\\Process\\Process'] as $needle) {
    if (!str_contains($source, $needle)) throw new RuntimeException('MISSING:' . $needle);
}
echo "EZS_TEST_007_OK\n";
