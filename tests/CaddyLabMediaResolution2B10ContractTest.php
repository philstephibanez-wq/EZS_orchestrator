<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$s=(string)file_get_contents($root.'/scripts/caddy-dev-lab-assistant-cutover.ps1');
if(str_contains($s,'EZS_CADDY_MEDIA_ROOT_ENV_MISSING_REFUSED'))throw new RuntimeException('MANUAL_ENV_GATE_REMAINS');
foreach(["\$devMediaRoot='H:\\EZScore_dev\\var\\storage\\stems'","\$env:EZSCORE_MEDIA_ROOT=\$devMediaRoot",'EZS_CADDY_EXISTING_DEV_MEDIA_DIRECTORY_MISSING','EZS_CADDY_LA_CUTOVER_OK_8790_8502_8852_8702_8712','EZS_CADDY_ROLLBACK_OLD_CONFIG_RESTORED'] as $needle){if(!str_contains($s,$needle))throw new RuntimeException('MISSING:'.$needle);}
echo "EZS_CADDY_LA_MEDIA_RESOLUTION_2_B10_CONTRACT_OK\n";
