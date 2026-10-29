<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/GlobalQueueLocation.php';
use Ezs\Web\Module\Coordination\GlobalQueueLocation;
$p=GlobalQueueLocation::path();
$expected=dirname(__DIR__).DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR.'queue'.DIRECTORY_SEPARATOR.'global.sqlite';
if($p!==$expected)throw new RuntimeException('CANONICAL_PATH');
$git=(string)file_get_contents(dirname(__DIR__).'/.gitignore');
if(!str_contains($git,'/data/queue/'))throw new RuntimeException('DATA_NOT_IGNORED');
if(!preg_match('/^4\.2c(\d+)$/',trim((string)file_get_contents(dirname(__DIR__).'/VERSION')),$v)|| (int)$v[1]<25)throw new RuntimeException('VERSION');
echo "EZS_GLOBAL_QUEUE_DATA_PATH_4_2C25_OK\n";
