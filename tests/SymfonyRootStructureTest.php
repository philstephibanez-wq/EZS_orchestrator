<?php
declare(strict_types=1);

$root = dirname(__DIR__);
foreach ([
    'bin/console','composer.json','composer.lock','src/Kernel.php','public/index.php',
    'config/bundles.php','config/routes.yaml','config/services.yaml',
    'src/Module/Infrastructure/Command/ProdFastcgiPreflightCommand.php',
    'src/Module/Infrastructure/ProdFastcgiPreflight.php',
    'templates/infrastructure/index.html.twig',
] as $relative) {
    if (!is_file($root.'/'.$relative)) {
        throw new RuntimeException('ROOT_SYMFONY_MISSING:'.$relative);
    }
}
$composer = json_decode((string)file_get_contents($root.'/composer.json'), true, 512, JSON_THROW_ON_ERROR);
if (($composer['name'] ?? null) !== 'ezs/orchestrator') {
    throw new RuntimeException('ROOT_SYMFONY_PACKAGE_INVALID');
}
$command = (string)file_get_contents($root.'/src/Module/Infrastructure/Command/ProdFastcgiPreflightCommand.php');
if (!str_contains($command, 'dirname(__DIR__, 4)')) {
    throw new RuntimeException('ROOT_PREFLIGHT_PATH_INVALID');
}
$kernel = (string)file_get_contents($root.'/src/Kernel.php');
if (!str_contains($kernel, 'MicroKernelTrait')) {
    throw new RuntimeException('ROOT_KERNEL_INVALID');
}
echo "SYMFONY_ROOT_STRUCTURE_OK\n";
