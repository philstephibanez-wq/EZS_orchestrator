<?php
declare(strict_types=1);
$r=dirname(__DIR__,2).'/web/config/caddy/';
$d=file_get_contents($r.'Caddyfile.dev');
$p=file_get_contents($r.'Caddyfile.prod');
$legacy=file_get_contents($r.'Caddyfile.dev-fastcgi-candidate');
if($d!==$legacy)throw new RuntimeException('DEV candidate changed');
foreach(['127.0.0.1:8790','127.0.0.1:8852','127.0.0.1:8502','php_fastcgi 127.0.0.1:8791','php_fastcgi 127.0.0.1:8602'] as $v)
 if(!str_contains($d,$v))throw new RuntimeException('DEV missing '.$v);
foreach(['127.0.0.1:8501','127.0.0.1:8510','/internal/media/auth','X-Forwarded-Proto https','X-Forwarded-Port 443','X-Forwarded-Host'] as $v)
 if(!str_contains($p,$v))throw new RuntimeException('PROD missing '.$v);
if(str_contains($d,'127.0.0.1:8501')||str_contains($p,'127.0.0.1:8502')||str_contains($p,'127.0.0.1:8790'))throw new RuntimeException('mixed Caddy');
echo "EZS_CADDY_CANONICAL_CONFIG_R1_OK\n";
