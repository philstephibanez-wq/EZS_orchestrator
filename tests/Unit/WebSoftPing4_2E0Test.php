<?php

declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\Controller\WebSoftPingController as Probe;
use PHPUnit\Framework\TestCase;

final class WebSoftPing4_2E0Test extends TestCase
{
    public function testFourLocalTargetsAndAccessRestrictions(): void
    {
        self::assertSame(['dev','lab','assistant','prod'],array_keys(Probe::definitions()));
        self::assertSame('http://127.0.0.1:8511/api/v1/service-status',Probe::definitions()['prod']);
        self::assertTrue(Probe::allowed('dev','127.0.0.1','127.0.0.1',8790));
        self::assertFalse(Probe::allowed('prod','127.0.0.1','127.0.0.1',8790));
        self::assertFalse(Probe::allowed('dev','example.com','127.0.0.1',8790));
        self::assertFalse(Probe::allowed('dev','127.0.0.1','8.8.8.8',8790));
        self::assertFalse(Probe::allowed('dev','127.0.0.1','127.0.0.1',8501));
    }
    public function testNotImplementedIsNotFatalAndApplicationKoIsDistinct(): void
    {
        self::assertSame('NON_IMPLEMENTE',Probe::classify(404,null,null)['state']);
        self::assertSame('NON_IMPLEMENTE',Probe::classify(405,null,null)['state']);
        self::assertSame('INJOIGNABLE',Probe::classify(null,null,'connection_or_timeout')['state']);
        self::assertSame('NON_CONFORME',Probe::classify(200,[],null)['state']);
        self::assertSame('ERREUR_HTTP',Probe::classify(503,null,null)['state']);
        self::assertSame('OK',Probe::classify(200,['schema'=>'ezs.service-status.v1','state'=>'OK','components'=>[]],null)['state']);
        self::assertSame('KO',Probe::classify(200,['schema'=>'ezs.service-status.v1','state'=>'KO','components'=>[]],null)['state']);
    }
    public function testNoMutationAndNoAutomaticRecovery(): void
    {
        $root=dirname(__DIR__,2);
        $php=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/WebSoftPingController.php');
        foreach(['Stop-Process','Start-Process','Start-Service','Stop-Service','fatalCutoverCandidate','shell_exec','proc_open'] as $forbidden) {
            self::assertStringNotContainsString($forbidden,$php);
        }
        $twig=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
        self::assertStringContainsString('ezs-web-soft.js',$twig);
        foreach(['dev','lab','assistant','prod'] as $site) self::assertStringContainsString('id="soft-'.$site.'"',$twig);
    }
}
