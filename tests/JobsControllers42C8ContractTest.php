<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c8')throw new RuntimeException('VERSION');
$controllers=[
 $root.'/src/Module/Infrastructure/Controller/LegacyReadOnlyController.php',
 $root.'/src/Module/Coordination/Controller/JobsPageController.php',
];
foreach($controllers as $path){
 $code=(string)file_get_contents($path);
 if(!str_contains($code,'use Ezs\\Web\\Module\\Coordination\\LegacyJobHistoryReader;'))throw new RuntimeException('IMPORT_MISSING:'.basename($path));
 exec(escapeshellarg(PHP_BINARY).' -l '.escapeshellarg($path).' 2>&1',$lines,$rc);
 if($rc!==0)throw new RuntimeException('PHP_PARSE:'.basename($path).':'.implode("\n",$lines));
}
$reader=$root.'/src/Module/Coordination/LegacyJobHistoryReader.php';
if(!is_file($reader))throw new RuntimeException('READER_MISSING');
echo "EZS_JOBS_CONTROLLERS_4_2C8_OK\n";
