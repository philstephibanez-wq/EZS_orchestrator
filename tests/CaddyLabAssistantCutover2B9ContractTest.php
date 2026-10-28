<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=(string)file_get_contents($r.'/scripts/caddy-dev-lab-assistant-cutover.ps1');
$v=(string)file_get_contents($r.'/scripts/v2_lifecycle.ps1');
foreach(["EZS_CADDY_EXISTING_DEV_MEDIA_DIRECTORY_MISSING","EZS_CADDY_OLD_OWNER_NOT_ATTESTED","EZS_CADDY_ROLLBACK_OLD_CONFIG_RESTORED","EZS_CADDY_LA_CUTOVER_OK_8790_8502_8852_8702_8712","EZS_CADDY_NEW_HTTP_FAILED"] as $a){if(!str_contains($s,$a))throw new RuntimeException("CUTOVER_MISSING:".$a);}
if(!str_contains($v,"function OwnedDevCaddy")||!str_contains($v,"Caddyfile.dev-lab-assistant-candidate"))throw new RuntimeException('LIFECYCLE_NOT_MIGRATED');
if(str_contains($s,'prod_mode.php')||str_contains($s,'H:\\EZScore\\'))throw new RuntimeException('PROD_SIDE_EFFECT');
echo "EZS_CADDY_LA_CUTOVER_2_B9_CONTRACT_OK\n";
