<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__,2).'/scripts/v2_lifecycle.ps1');
foreach (['BACKEND_8791_STILL_LISTENING','BACKEND_8791_UNEXPECTED_PID','OWNERSHIP_MISMATCH=','metadata preserved','if ($null -ne $remaining)'] as $term) {
    if (!str_contains($s,$term)) throw new RuntimeException('Missing '.$term);
}
$stop=substr($s,strpos($s,"if (\$Action -eq 'stop')"),strpos($s,"if (\$null -ne \$state)",strpos($s,"if (\$Action -eq 'stop')"))-strpos($s,"if (\$Action -eq 'stop')"));
if(strpos($stop,'$remaining = Listener 8791') > strpos($stop,'$state.php_pid = 0')) throw new RuntimeException('unsafe pid clear');
echo "EZS_V2_BACKEND_OWNERSHIP_GUARD_OK\n";
