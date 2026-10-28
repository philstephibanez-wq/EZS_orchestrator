<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$dev=(string)file_get_contents($root.'/scripts/start.ps1');
$start=(string)file_get_contents($root.'/scripts/start.ps1');
$stop=(string)file_get_contents($root.'/scripts/stop.ps1');
$anchor=strpos($dev,"if (\$null -ne \$s) {");
$verify=strpos($dev,"EZS_DEV_ALREADY_RUNNING_VERIFIED");
$refuse=strpos($dev,"EZS_START_REFUSED_STALE_OR_FOREIGN_ORCHESTRATOR_BACKEND");
$launch=strpos($dev,"\$backend = Start-Process -FilePath \$php -ArgumentList '-b 127.0.0.1:8791' -WorkingDirectory \$root -WindowStyle Hidden -PassThru -RedirectStandardError");
if($verify===false||$refuse===false||$launch===false||$verify>$launch||$refuse>$launch)throw new RuntimeException('IDEMPOTENT_DEV_START_GUARD_MISSING');
foreach (['Port-Owned 8791','Port-Owned 8790','Port-Owned 8502','Port-Owned 8852', 'EZS_DEV_ALREADY_RUNNING_VERIFIED'] as $token){
 if(!str_contains($dev,$token))throw new RuntimeException('DEV_OWNER_CHECK_MISSING:'.$token);
}
if(!str_contains($start,"Invoke-EzsRootLifecycle -Action start"))throw new RuntimeException('DEV_START_ENTRY_CHANGED');
if(!str_contains($stop,'prod_mode.php')||!str_contains($stop,'maintenance'))throw new RuntimeException('PROD_MAINTENANCE_ON_STOP_REGRESSION');
$executableLines=array_filter(explode("\n",$start),static fn(string $line): bool => !str_starts_with(ltrim($line),'#'));
$executableStart=implode("\n",$executableLines);
if(str_contains($executableStart,'gateway-php.json')||str_contains($executableStart,'18515')||str_contains($executableStart,'-Target gateway'))throw new RuntimeException('PROD_GATEWAY_START_REGRESSION');
echo "EZS_DEV_START_IDEMPOTENCY_2_B0_CONTRACT_OK\n";
