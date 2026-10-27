<?php
declare(strict_types=1);
$r=dirname(__DIR__,2);
$active=file_get_contents($r.'/web/config/caddy/Caddyfile.dev-preflight');
$candidate=file_get_contents($r.'/web/config/caddy/Caddyfile.dev-fastcgi-candidate');
if(!str_starts_with($candidate,$active))throw new RuntimeException('active sites modified');
if(substr_count($candidate,'http://127.0.0.1:8502')!==1)throw new RuntimeException('invalid facade');
foreach(['forward_auth 127.0.0.1:8502','uri /internal/media/auth','php_fastcgi 127.0.0.1:8602','root * {$EZSCORE_MEDIA_ROOT}','uri strip_prefix /media','root * H:/EZScore_dev/public'] as $needle){
 if(!str_contains($candidate,$needle))throw new RuntimeException('missing '.$needle);
}
if(str_contains($candidate,'http://127.0.0.1:8501')||str_contains($candidate,'127.0.0.1:8510'))throw new RuntimeException('PROD mixed');
echo "EZS_CADDY_8502_FASTCGI_AUTH_CANDIDATE_OK\n";
