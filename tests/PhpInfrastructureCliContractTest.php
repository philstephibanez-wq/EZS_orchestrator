<?php
declare(strict_types=1);
$p=(string)file_get_contents(__DIR__.'/../bin/infrastructure.php');
foreach (['EZS_PHP_INFRA_PREFLIGHT_OK','ezs.infrastructure.status.php.v1','Caddyfile.prod-internal-candidate','listeners_ready','state_present'] as $s) if(!str_contains($p,$s))throw new RuntimeException('PHP_INFRA_CLI_CONTRACT_MISSING:'.$s);
foreach (['Stop-Process','Start-Process','powershell.exe'] as $s) if(str_contains($p,$s)) throw new RuntimeException('PHP_INFRA_CLI_PROCESS_MUTATION:'.$s);
echo "EZS_PHP_INFRA_CLI_CONTRACT_OK\n";
