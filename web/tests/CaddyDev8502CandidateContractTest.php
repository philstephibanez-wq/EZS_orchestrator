<?php
declare(strict_types=1);
$root=dirname(__DIR__,2);
$active=file_get_contents($root.'/web/config/caddy/Caddyfile.dev-preflight');
$candidate=file_get_contents($root.'/web/config/caddy/Caddyfile.dev-candidate');
if(!str_starts_with($candidate,$active)) throw new RuntimeException('Live routes modified in candidate');
if(substr_count($candidate,'http://127.0.0.1:8502')!==1) throw new RuntimeException('DEV route missing');
foreach(['forward_auth 127.0.0.1:8602','uri /internal/media/auth','root * {$EZSCORE_MEDIA_ROOT}','uri strip_prefix /media','reverse_proxy 127.0.0.1:8602'] as $x) if(!str_contains($candidate,$x)) throw new RuntimeException('DEV protection missing '.$x);
if(str_contains($candidate,'8501') || str_contains($candidate,'8510')) throw new RuntimeException('PROD mixed with DEV');
echo "EZS_CADDY_DEV_8502_CANDIDATE_CONTRACT_OK\n";
