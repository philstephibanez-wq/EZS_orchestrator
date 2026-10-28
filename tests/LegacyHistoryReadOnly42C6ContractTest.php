<?php
declare(strict_types=1);
require dirname(__DIR__).'/src/Module/Coordination/LegacyJobHistoryReader.php';
use Ezs\Web\Module\Coordination\LegacyJobHistoryReader;
if(!preg_match('/^4\\.2c[6-9][0-9]*$/',trim((string)file_get_contents(dirname(__DIR__).'/VERSION'))))throw new RuntimeException('VERSION_SERIES');
$root=sys_get_temp_dir().'/ezs_jobs_readonly_'.bin2hex(random_bytes(6));
$dir=$root.'/runtime/jobs/dev/14/run-1';mkdir($dir,0700,true);
try {
  file_put_contents($dir.'/result.json',json_encode(['job_id'=>14,'kind'=>'stems','state'=>'finalize_error','analysis_returncode'=>0,'finalize_status'=>'error','song_title'=>'Test']));
  $reader=new LegacyJobHistoryReader($root);$rows=$reader->recent();
  if(count($rows)!==1||$rows[0]['state']!=='finalize_error'||$rows[0]['analysis_returncode']!==0)throw new RuntimeException('HISTORY_RESULT');
  if($reader->recent(1)[0]['job_id']!==14)throw new RuntimeException('LIMIT');
  if(!is_file($dir.'/result.json'))throw new RuntimeException('UNEXPECTED_MUTATION');
  echo "EZS_LEGACY_HISTORY_READONLY_4_2C6_OK\n";
} finally { @unlink($dir.'/result.json');@rmdir($dir);@rmdir(dirname($dir));@rmdir(dirname(dirname($dir)));@rmdir(dirname(dirname(dirname($dir))));@rmdir(dirname(dirname(dirname(dirname($dir)))));@rmdir($root); }
