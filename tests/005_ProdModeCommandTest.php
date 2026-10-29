<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$command = (string) file_get_contents($root . '/src/Module/Infrastructure/ProdModeCommand.php');
$service = (string) file_get_contents($root . '/src/Module/Infrastructure/ProdModeService.php');
foreach (['AsCommand', 'ezs:prod:mode', 'ProdModeService', "['status', 'maintenance', 'normal']", "'gateway_online'", 'JSON_THROW_ON_ERROR'] as $needle) {
    if (!str_contains($command, $needle)) throw new RuntimeException('COMMAND_CONTRACT_MISSING:' . $needle);
}
if (!str_contains($service, 'function apply(') || !str_contains($service, 'function inspect(')) {
    throw new RuntimeException('PROD_MODE_SERVICE_CONTRACT_MISSING');
}
if (is_file($root . '/bin/prod_mode.php')) throw new RuntimeException('PROD_MODE_LEGACY_STILL_PRESENT');
echo "EZS_TEST_005_OK\n";
