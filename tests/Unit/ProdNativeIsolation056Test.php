<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class ProdNativeIsolation056Test extends TestCase
{
    public function testOneProdCaddyAndIsolatedFastcgiProcesses():void
    {
        $specs=NativeWindowsLifecycle::prodSpecs();
        self::assertSame(['prod_backend','prod_gateway','prod_caddy'],array_keys($specs));
        self::assertSame([8510,8511],$specs['prod_caddy']['additional_ports']);
        self::assertSame(8501,$specs['prod_caddy']['port']);
        self::assertSame('H:/EZScore',$specs['prod_backend']['cwd']);
        foreach(NativeWindowsLifecycle::specs() as $spec){
            self::assertNotContains($spec['port'],[8501,8510,8511,8512,18515]);
        }
    }

    public function testProdProcessRequiresAllCaddyPortAttestations():void
    {
        $s=NativeWindowsLifecycle::prodSpecs()['prod_caddy'];
        $p=['pid'=>100,'created'=>'X','executable'=>$s['exe'],
            'command'=>'"'.$s['exe'].'" "run" "--config" "H:/EZS_orchestrator/config/caddy/Caddyfile.prod" "--adapter" "caddyfile"'];
        $record=['pid'=>100,'created'=>'X'];
        self::assertTrue(NativeWindowsLifecycle::attest($record,$s,$p,[8501=>[100],8510=>[100],8511=>[100]]));
        self::assertFalse(NativeWindowsLifecycle::attest($record,$s,$p,[8501=>[100],8510=>[100],8511=>[200]]));
    }

    public function testProdCaddyConfigHasOneProcessConfigurationAndNoDevPort():void
    {
        $c=(string)file_get_contents(dirname(__DIR__,2).'/config/caddy/Caddyfile.prod');
        foreach([':8501 {',':8510 {',':8511 {'] as $site) self::assertStringContainsString($site,$c);
        self::assertStringNotContainsString(':8502 {',$c);
        self::assertStringContainsString('php_fastcgi 127.0.0.1:18515',$c);
        self::assertStringContainsString('php_fastcgi 127.0.0.1:8512',$c);
    }
    public function testProdNativeRecoversOnlyCaddyAfterCrashAndRefusesForeignPid():void
    {
        $dir=sys_get_temp_dir().'/ezs-prod-'.bin2hex(random_bytes(5));
        self::assertTrue(mkdir($dir));
        $alive=[];$next=20000;$killed=[];
        $specs=NativeWindowsLifecycle::prodSpecs();
        $inventory=static function() use (&$alive):array {
            $rows=[];
            foreach($alive as $pid=>$spec){
                $args=[$spec['exe'],...NativeWindowsLifecycle::spawnArguments($spec['args'])];
                $rows[]=['pid'=>$pid,'created'=>'stamp-'.$pid,'executable'=>$spec['exe'],
                    'command'=>implode(' ',array_map(static fn($x)=>'"'.$x.'"',$args))];
            }
            return $rows;
        };
        $listeners=static function() use (&$alive):array {
            $ports=[];
            foreach($alive as $pid=>$spec){
                foreach([$spec['port'],...($spec['additional_ports']??[])] as $port)$ports[$port]=[$pid];
            }
            return $ports;
        };
        $spawn=static function(string $exe,string $args,string $cwd) use (&$alive,&$next,$specs):int {
            foreach($specs as $spec){
                if($spec['exe']===$exe && $spec['args']===$args && $spec['cwd']===$cwd){
                    $alive[++$next]=$spec;
                    return $next;
                }
            }
            throw new RuntimeException('unexpected spawn');
        };
        $terminate=static function(int $pid) use (&$alive,&$killed):bool {
            $killed[]=$pid;unset($alive[$pid]);return true;
        };
        try{
            $svc=new NativeWindowsLifecycle($inventory,$listeners,$spawn,$terminate,$dir,
                static fn():bool=>true, static fn():?int=>null,'prod');
            $first=$svc->startGroup('prod');
            self::assertSame(['prod_backend','prod_gateway','prod_caddy'],array_keys($first));
            self::assertSame([],$svc->startGroup('prod'));
            unset($alive[$first['prod_caddy']]);
            $second=$svc->startGroup('prod');
            self::assertSame(['prod_caddy'],array_keys($second));
            self::assertSame($first['prod_backend'],array_search($specs['prod_backend'],$alive,true));
            self::assertSame($first['prod_gateway'],array_search($specs['prod_gateway'],$alive,true));
            self::assertSame([],$killed);
            // PID reutilise avec autre commande : ni adoption ni termination.
            $stolen=$second['prod_caddy'];
            $alive[$stolen]=['port'=>8501,'additional_ports'=>[8510,8511],
                'exe'=>'C:/foreign.exe','cwd'=>'C:/foreign','args'=>'-b 127.0.0.1:8501'];
            try{
                $svc->startGroup('prod');
                self::fail('foreign pid must be refused');
            }catch(RuntimeException $failure){
                self::assertStringContainsString('EZS_NATIVE_IDENTITY_UNVERIFIED_prod_caddy',$failure->getMessage());
            }
            self::assertSame([],$killed);
        }finally{
            foreach(glob($dir.'/*')?:[] as $file)if(is_file($file))unlink($file);
            rmdir($dir);
        }
    }

}
