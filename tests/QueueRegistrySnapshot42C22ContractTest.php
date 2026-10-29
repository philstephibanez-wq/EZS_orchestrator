<?php
declare(strict_types=1);
require dirname(__DIR__).'/vendor/autoload.php';
use Ezs\Web\Module\Coordination\GlobalQueueSnapshot;
if(trim(file_get_contents(dirname(__DIR__).'/VERSION'))!=='4.2c22')throw new RuntimeException('VERSION');
$a=GlobalQueueSnapshot::read(dirname(__DIR__).'/tests/does-not-exist-42c22.db');
if($a['available']!==false)throw new RuntimeException('MISSING_DB_NOT_CLOSED');
if(!extension_loaded('pdo_sqlite'))throw new RuntimeException('SQLITE_UNAVAILABLE');
$f=tempnam(sys_get_temp_dir(),'ezsq_');unlink($f);
$db=new PDO('sqlite:'.$f);$db->exec('CREATE TABLE jobs (target TEXT, job_id INTEGER, kind TEXT, priority INTEGER, state TEXT, updated_at TEXT, created_at TEXT)');
$db->exec("INSERT INTO jobs VALUES ('lab',193,'profile',50,'queued','2026-10-29','2026-10-29')");
$db=null;
try {
  $result=GlobalQueueSnapshot::read($f);
  if(!$result['available']||count($result['jobs'])!==1||(int)$result['jobs'][0]['job_id']!==193)throw new RuntimeException('SNAPSHOT');
} finally {unlink($f);}
echo "EZS_QUEUE_REGISTRY_SNAPSHOT_4_2C22_OK\n";
