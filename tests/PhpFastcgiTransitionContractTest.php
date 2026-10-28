<?php
declare(strict_types=1);
require_once __DIR__.'/../src/Module/Infrastructure/FastcgiTransitionJournal.php';
use Ezs\Web\Module\Infrastructure\FastcgiTransitionJournal as J;
$dir=sys_get_temp_dir().'/ezs-contract-'.bin2hex(random_bytes(4));
try {
 $a=J::observe($dir,10,[10],'php-cgi.exe');
 $b=J::observe($dir,10,[10],'php-cgi.exe');
 $c=J::observe($dir,10,[],null);
 if(!$a['changed']||$b['changed']||!$c['changed']||$c['current']['ready'])throw new RuntimeException('TRANSITION_CONTRACT_FAILED');
 $lines=file($dir.'/fastcgi-observations.jsonl',FILE_IGNORE_NEW_LINES|FILE_SKIP_EMPTY_LINES);
 if(count($lines)!==2)throw new RuntimeException('TRANSITION_COUNT_FAILED');
 echo "EZS_FASTCGI_TRANSITION_CONTRACT_OK\n";
} finally {
 foreach(glob($dir.'/*')?:[] as $f)unlink($f);
 if(is_dir($dir))rmdir($dir);
}
