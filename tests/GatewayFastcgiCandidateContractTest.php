<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$config=(string)file_get_contents($root.'/config/caddy/Caddyfile.gateway-php-candidate');
$preflight=(string)file_get_contents($root.'/bin/gateway_fastcgi_candidate.php');
if(!str_contains($config,':18514')||!str_contains($config,'18515')||!str_contains($config,'bind 127.0.0.1')||!str_contains($config,'admin off'))throw new RuntimeException('GATEWAY_CANDIDATE_NOT_ISOLATED');
if(str_contains($config,':8510')||str_contains($config,':8501'))throw new RuntimeException('PROD_PORT_FORBIDDEN');
if(!str_contains($preflight,"'prod_cutover_authorized'=>false"))throw new RuntimeException('UNSAFE_CUTOVER_GATE');
echo "EZS_GATEWAY_FASTCGI_CANDIDATE_CONTRACT_OK\n";
