<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
$a=strpos($s,'function Invoke-EzsProdLifecycle');
$p=substr($s,$a,10000);
foreach(['function ProdTcp','function ProdIdentity','EZS_PROD_STALE_STATE_AFTER_REBOOT_CLEARED','EZS_PROD_REFUSED_EXISTING_STATE','ProdIdentity 8512','ProdIdentity 8511','ProdIdentity 8510','ProdIdentity 8501','SetMode $true'] as $v){if(!str_contains($p,$v))throw new RuntimeException('MISSING '.$v);}
echo "EZS_PROD_REBOOT_4_2C46_OK\n";