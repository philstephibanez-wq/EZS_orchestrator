<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/app-control.ps1');
foreach (["if (\$Action -eq 'restart')",'} finally {','APP_CONTROL_OK APP=','function AssertOrchestrator {','$caddy = @(& $CaddyCheck -Action status)',"PID=[1-9][0-9]*\$'"] as $needle) {
 if(substr_count($s,$needle)!==1) throw new RuntimeException('non unique/missing: '.$needle);
}
if(str_contains($s,'$LASTEXITCODE -ne 0')||str_contains($s,"\n) {\n"))throw new RuntimeException('duplicated segment');
echo "EZS_APP_CONTROL_HOTFIX_STRUCTURE_OK\n";
