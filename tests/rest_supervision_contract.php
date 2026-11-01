<?php

declare(strict_types=1);

require dirname(__DIR__).'/vendor/autoload.php';
use Ezs\Web\Module\Infrastructure\Controller\RestSupervisionController as C;
use Symfony\Component\HttpFoundation\Request;

$dir = sys_get_temp_dir().'/ezs_rest_test_'.bin2hex(random_bytes(6));
if (!mkdir($dir,0700,true)) throw new RuntimeException('test_temp_failed');
$file=$dir.'/state.json';
try {
    if(C::readState($file)['state']!=='IDLE')throw new RuntimeException('idle_failed');
    C::writeState($file,['state'=>'RUNNING','id'=>str_repeat('a',32),'started_at'=>1234]);
    if(C::readState($file)['id']!==str_repeat('a',32))throw new RuntimeException('roundtrip_failed');
    $r=Request::create('http://127.0.0.1:8790/api/v2/infrastructure/rest-supervision');
    // Public endpoint must refuse non-loopback and non-DEV environments.
    $_SERVER['APP_ENV']='prod';
    if(C::allowed($r)!==false)throw new RuntimeException('permission_failed');
    $r=Request::create('http://example.com:8790/api/v2/infrastructure/rest-supervision');
    if(C::allowed($r)!==false)throw new RuntimeException('permission_failed');
    file_put_contents($file,'{bad json');
    try {C::readState($file);throw new RuntimeException('invalid_state_not_refused');}
    catch (RuntimeException $e) {if($e->getMessage()==='invalid_state_not_refused')throw $e;}
    echo "EZS_REST_SUPERVISION_CONTRACT_OK\n";
} finally {foreach(glob($dir.'/*')?:[] as $p)unlink($p);rmdir($dir);}
