<?php
$src=file_get_contents(dirname(__DIR__,2).'/scripts/caddy_dev_shared.ps1');
foreach(['instance.lock','CADDY_DEV_REUSED','CADDY_DEV_CONFLICT','Port 8852','Identity $p.Id'] as $item){if(!str_contains($src,$item))throw new RuntimeException($item);}
if(str_contains($src,'8501')||str_contains($src,'Stop-Process -Name'))throw new RuntimeException('unsafe');
echo "CADDY_DEV_SHARED_CONTRACT_OK\n";
