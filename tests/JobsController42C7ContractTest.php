<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c7')throw new RuntimeException('VERSION');
$path=$root.'/src/Module/Infrastructure/Controller/LegacyReadOnlyController.php';
$code=(string)file_get_contents($path);
if(!str_contains($code,'use Ezs\\Web\\Module\\Coordination\\LegacyJobHistoryReader;'))throw new RuntimeException('HISTORY_IMPORT_MISSING');
if(!str_contains($code,"['ok' => false, 'error' => 'forbidden'], 403"))throw new RuntimeException('LOOPBACK_GUARD_MISSING');
if(!str_contains($code,"'live_queue' => false"))throw new RuntimeException('FALSE_LIVE_STATE');
$command=escapeshellarg(PHP_BINARY).' -l '.escapeshellarg($path);
exec($command.' 2>&1',$output,$status);
if($status!==0)throw new RuntimeException('CONTROLLER_PARSE_ERROR:'.implode("\n",$output));
echo "EZS_JOBS_CONTROLLER_4_2C7_OK\n";
