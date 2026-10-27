<?php
$c=file_get_contents(__DIR__.'/../config/caddy/Caddyfile.prod');
if(strpos($c,':8501 {')===false || strpos($c,'bind 127.0.0.1')===false || strpos($c,'http://127.0.0.1:8501 {')!==false){throw new RuntimeException('PROD_HOST_MATCH_FAILED');}
echo "EZS_PROD_HOST_OK\n";
