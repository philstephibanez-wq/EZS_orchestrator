<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/config/caddy/Caddyfile.gateway-php-candidate');
foreach(['header_up X-EZS-Original-URI {http.request.orig_uri}','header_up X-Forwarded-Proto {http.request.header.X-Forwarded-Proto}','bind 127.0.0.1'] as $p)if(!str_contains($s,$p))throw new RuntimeException('CANDIDATE_HEADER_MISSING:'.$p);
echo "EZS_GATEWAY_FORWARDED_PROTO_CONTRACT_OK\n";
