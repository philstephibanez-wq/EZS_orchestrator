<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Tester\CommandTester;
use Ezs\Web\Module\Infrastructure\EcosystemEntryCommand;
use Ezs\Web\Module\Infrastructure\EcosystemStopCommand;
final class DevAppsRecovery024Test extends TestCase {
    public function testComposerSymfonyPlansNeverMutateRuntime():void {
        $app=new Application();
        $app->add(new EcosystemEntryCommand());
        $app->add(new EcosystemStopCommand());
        foreach(['ezs:ecosystem:start','ezs:ecosystem:stop'] as $name){
            $tester=new CommandTester($app->find($name));
            self::assertSame(0,$tester->execute(['--plan'=>true]));
            self::assertStringContainsString('EZS_ECOSYSTEM_PLAN=', $tester->getDisplay());
        }
    }
}
