<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\NativeSiteObservation;
use PHPUnit\Framework\TestCase;

final class InfrastructureStateTriadContractTest extends TestCase
{
    public function testBadgesClassifyUsingDesiredAndNativeState(): void
    {
        $js = (string)file_get_contents(dirname(__DIR__, 2).'/public/assets/ezs-infrastructure.js');
        self::assertStringContainsString("native === 'STOPPED' && desired === 'STOPPED'", $js);
        self::assertStringContainsString("native === 'RUNNING' && desired === 'RUNNING'", $js);
        foreach (['ONLINE','OFFLINE','ERREUR'] as $token) self::assertStringContainsString("'".$token."'", $js);
        self::assertStringContainsString(".attr('aria-disabled', online ? 'false' : 'true')", $js);
        self::assertStringContainsString("if ($(this).attr('aria-disabled') === 'true') event.preventDefault();", $js);
    }

    public function testNativeStatusSeparatesDesiredFromObservedState(): void
    {
        $stopped = NativeSiteObservation::classify('dev', 'SITE=dev INTENT=RUNNING OWNED=0 LISTENERS=0');
        self::assertSame('STOPPED', $stopped['state']);
        self::assertSame('RUNNING', $stopped['desired']);
        $running = NativeSiteObservation::classify('lab', 'SITE=lab INTENT=STOPPED OWNED=1 LISTENERS=2');
        self::assertSame('RUNNING', $running['state']);
        self::assertSame('STOPPED', $running['desired']);
        $source=(string)file_get_contents(dirname(__DIR__,2).'/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("'dev'=>".'$observation'."->observe('dev')", $source);
        self::assertStringContainsString("'lab'=>".'$observation'."->observe('lab')", $source);
    }
}
