<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;

final class NativeDeadRecordRecovery055Test extends TestCase
{
    public function testDeadLabRecordCanBeReconciledWithoutTouchingAssistant(): void
    {
        $dir = sys_get_temp_dir().'/ezs-r8f22-'.bin2hex(random_bytes(6));
        self::assertTrue(mkdir($dir));
        $alive = [];
        $next = 8000;
        $make = static function () use (&$alive, &$next, $dir): NativeWindowsLifecycle {
            return new NativeWindowsLifecycle(
                static function () use (&$alive): array {
                    $rows=[];
                    foreach($alive as $pid=>$spec) {
                        $tokens=[$spec['exe'],...NativeWindowsLifecycle::spawnArguments($spec['args'])];
                        $rows[]=['pid'=>$pid,'created'=>'test-created-'.$pid,'executable'=>$spec['exe'],
                            'command'=>implode(' ',array_map(static fn($a)=>'"'.$a.'"',$tokens))];
                    }
                    return $rows;
                },
                static function () use (&$alive): array {
                    $ports=[];
                    foreach($alive as $pid=>$spec)$ports[$spec['port']]=[$pid];
                    return $ports;
                },
                static function (string $exe,string $args,string $cwd) use (&$alive,&$next):int {
                    foreach(NativeWindowsLifecycle::specs() as $spec) {
                        if($spec['exe']===$exe && $spec['args']===$args && $spec['cwd']===$cwd) {
                            $alive[++$next]=$spec;
                            return $next;
                        }
                    }
                    throw new RuntimeException('unknown spawn');
                },
                static function (int $pid) use (&$alive):bool {unset($alive[$pid]);return true;},
                $dir,
                static fn():bool=>true,
                static fn():?int=>null
            );
        };
        try {
            $svc=$make();
            $lab=$svc->startGroup('lab');
            $assistant=$svc->startGroup('assistant');
            unset($alive[$lab['lab']]); // Panne brutale, état persistant non modifié.
            self::assertSame('ABSENT',$svc->status()['lab']);
            $new=$svc->startGroup('lab');
            self::assertArrayHasKey('lab',$new);
            self::assertNotSame($lab['lab'],$new['lab']);
            self::assertArrayHasKey($assistant['assistant'],$alive);
            self::assertSame('ATTESTED',$svc->status()['lab']);
            self::assertStringContainsString('DEAD_RECORD lab PID='.$lab['lab'],(string)file_get_contents($dir.'/native-reconciled.log'));
        } finally {
            foreach(glob($dir.'/*')?:[] as $file) if(is_file($file))unlink($file);
            rmdir($dir);
        }
    }
}
