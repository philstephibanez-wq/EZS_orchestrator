<?php
declare(strict_types=1);
$r=dirname(__DIR__);
$s=(string)file_get_contents($r.'/bin/gateway_fastcgi_autotest.php');
$c=(string)file_get_contents($r.'/config/caddy/Caddyfile.gateway-php-candidate');
$p=(string)file_get_contents($r.'/runtime_components/prod_gateway_php/router.php');
foreach(['18511','18514','18515','FASTCGI_URI_OR_HEADERS_MISMATCH','array_reverse($jobs)','EZS_GATEWAY_FASTCGI_AUTOTEST_OK'] as $token)if(!str_contains($s,$token))throw new RuntimeException('MISSING_TEST_TOKEN_'.$token);
if(!str_contains($c,'X-EZS-Original-URI {http.request.orig_uri}')||!str_contains($p,'HTTP_X_EZS_ORIGINAL_URI'))throw new RuntimeException('MISSING_ORIGINAL_URI_TRANSPORT');
if(str_contains($s,'taskkill')||str_contains($s,'Stop-Process'))throw new RuntimeException('UNSAFE_PROCESS_KILL');
echo "EZS_GATEWAY_FASTCGI_AUTOTEST_CONTRACT_OK\n";
