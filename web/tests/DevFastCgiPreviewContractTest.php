<?php
declare(strict_types=1);
$root=dirname(__DIR__,2);
$caddy=file_get_contents($root.'/web/config/caddy/Caddyfile.dev-preflight');
$ps=file_get_contents($root.'/scripts/ezscore_dev_preview.ps1');
foreach (['127.0.0.1:8790','127.0.0.1:8852','127.0.0.1:8862','H:/EZScore_dev/public','respond @protected'] as $term) {
 if (!str_contains($caddy,$term)) throw new RuntimeException('missing:'.$term);
}
if(str_contains($caddy,'8501')||str_contains($caddy,'8502'))throw new RuntimeException('production_or_public_port_modified');
if(!str_contains($ps,'Stop-Process') || !str_contains($ps,'Owned $state.pid') || !str_contains($ps,'OwningProcess'))throw new RuntimeException('unsafe_lifecycle');
echo "DEV_FASTCGI_PREVIEW_CONTRACT_OK\n";
