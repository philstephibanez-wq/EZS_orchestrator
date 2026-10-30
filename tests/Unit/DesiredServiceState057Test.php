<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\DesiredServiceState;
use Ezs\Web\Module\Infrastructure\ServiceSupervisorCommand;

final class DesiredServiceState057Test extends TestCase
{
    public function testStoppedIsDefaultAndIntentPersists():void
    {
        $dir=sys_get_temp_dir().'/ezs-intent-'.bin2hex(random_bytes(5));
        self::assertTrue(mkdir($dir));
        try{
            $path=$dir.'/desired.json';
            $state=new DesiredServiceState($path);
            self::assertSame(DesiredServiceState::STOPPED,$state->get('prod'));
            self::assertSame([],ServiceSupervisorCommand::planned($state->all()));
            $state->setMany(['dev'=>DesiredServiceState::RUNNING,'prod'=>DesiredServiceState::RUNNING]);
            self::assertSame(['dev','prod'],ServiceSupervisorCommand::planned((new DesiredServiceState($path))->all()));
            $state->set('prod',DesiredServiceState::STOPPED);
            self::assertSame(['dev'],ServiceSupervisorCommand::planned((new DesiredServiceState($path))->all()));
        }finally{
            foreach(glob($dir.'/*')?:[] as $file)unlink($file);
            rmdir($dir);
        }
    }

    public function testBackoffIsBounded():void
    {
        self::assertSame(1030,ServiceSupervisorCommand::nextAttempt(1,1000));
        self::assertSame(1060,ServiceSupervisorCommand::nextAttempt(2,1000));
        self::assertSame(1120,ServiceSupervisorCommand::nextAttempt(3,1000));
        self::assertSame(1300,ServiceSupervisorCommand::nextAttempt(20,1000));
    }
}
