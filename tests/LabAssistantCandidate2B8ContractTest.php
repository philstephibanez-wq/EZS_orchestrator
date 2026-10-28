<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$c=(string)file_get_contents($root.'/config/caddy/Caddyfile.dev-lab-assistant-candidate');
$s=(string)file_get_contents($root.'/scripts/start.ps1');
$active=(string)file_get_contents($root.'/config/caddy/Caddyfile.dev-root-candidate');
foreach(['http://127.0.0.1:8702','H:/EZStudio_lab/public','php_fastcgi 127.0.0.1:8701','http://127.0.0.1:8712','H:/EZStudioLab_assistant/public','php_fastcgi 127.0.0.1:8713'] as $a){if(!str_contains($c,$a))throw new RuntimeException('CANDIDATE_MISSING '.$a);}
if(str_contains($active,'http://127.0.0.1:8702')||str_contains($active,'http://127.0.0.1:8712'))throw new RuntimeException('ACTIVE_CADDY_MODIFIED');
foreach(["ValidateSet('preflight','start','status')",'EZS_LA_REFUSED_UNOWNED_PORT_','EZS_LA_BACKENDS_READY_8701_8713','Attested $t.port','-WindowStyle Hidden'] as $a){if(!str_contains($s,$a))throw new RuntimeException('START_MISSING '.$a);}
foreach(['prod_mode.php','H:\\EZScore','Stop-Process -Id $caddy','caddy reload','Caddyfile.prod','EZSTUDIO-XPS'] as $a){if(str_contains($s,$a))throw new RuntimeException('FORBIDDEN '.$a);}
echo "EZS_LA_CANDIDATE_2_B8_CONTRACT_OK\n";
