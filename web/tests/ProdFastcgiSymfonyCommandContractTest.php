<?php
declare(strict_types=1);

$root = dirname(__DIR__, 2);
$command = file_get_contents($root.'/web/src/Module/Infrastructure/Command/ProdFastcgiPreflightCommand.php');
$preflight = file_get_contents($root.'/web/src/Module/Infrastructure/ProdFastcgiPreflight.php');
foreach (["ezs:prod:fastcgi-preflight", "ProdFastcgiPreflight::inspect", "Command::FAILURE"] as $required) {
    if (!str_contains($command, $required)) throw new RuntimeException('COMMAND_CONTRACT_MISSING:'.$required);
}
foreach (['proc_open(', 'shell_exec(', 'exec(', 'passthru('] as $forbidden) {
    if (str_contains($preflight, $forbidden)) throw new RuntimeException('PREFLIGHT_MUTATING:'.$forbidden);
}
echo "PROD_FASTCGI_SYMFONY_COMMAND_CONTRACT_OK\n";
