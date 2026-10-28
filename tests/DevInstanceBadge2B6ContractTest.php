<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
if(!str_contains($s,"\$env:EZSCORE_INSTANCE='dev'"))throw new RuntimeException('DEV_INSTANCE_ENV_NOT_EXPORTED');
if(strpos($s,"\$env:EZSCORE_INSTANCE='dev'") > strpos($s,'Start-Process -FilePath $binary'))throw new RuntimeException('DEV_INSTANCE_ENV_TOO_LATE');
if(str_contains($s,"\$env:EZSCORE_INSTANCE='prod'"))throw new RuntimeException('DEV_WRONG_INSTANCE');
echo "EZS_DEV_INSTANCE_BADGE_2_B6_CONTRACT_OK\n";
