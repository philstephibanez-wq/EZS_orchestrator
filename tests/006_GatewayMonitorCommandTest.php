<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/vendor/autoload.php';
require_once dirname(__DIR__) . '/src/Module/Infrastructure/GatewayMonitorCommand.php';
$class = Ezs\Web\Module\Infrastructure\GatewayMonitorCommand::class;
if (!method_exists($class, 'snapshot')) throw new RuntimeException('MISSING_GATEWAY_SNAPSHOT');
$source = (string) file_get_contents(dirname(__DIR__) . '/src/Module/Infrastructure/GatewayMonitorCommand.php');
foreach (['ezs:gateway:monitor', 'READ_ONLY', 'safe_to_cutover', 'WindowsPortOwnership::snapshot'] as $needle) {
    if (!str_contains($source, $needle)) throw new RuntimeException('MISSING:' . $needle);
}
echo "EZS_TEST_006_OK\n";
